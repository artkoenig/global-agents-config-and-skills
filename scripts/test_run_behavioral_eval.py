#!/usr/bin/env python3
"""Unit tests for scripts/run_behavioral_eval.py.

The `claude -p` subprocess calls are the only non-deterministic part, so they
are mocked at the run_executor / run_grader / make_sandbox seams. Everything
else — discovery, transcript rendering, grading extraction, threshold logic,
per-case error handling, suite aggregation, and exit codes — is exercised
directly.

Run: python3 scripts/test_run_behavioral_eval.py
"""

import json
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_behavioral_eval as runner  # noqa: E402


def _grading(pass_rate: float) -> dict:
    total = 2
    passed = round(pass_rate * total)
    return {
        "expectations": [],
        "summary": {"passed": passed, "failed": total - passed,
                    "total": total, "pass_rate": pass_rate},
    }


class DiscoverEvalFiles(unittest.TestCase):
    def test_finds_all_three_locations(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            targets = [
                root / "skills" / "issue-tracker" / "evals" / "evals.json",
                root / "agents" / "test-runner" / "evals" / "evals.json",
                root / "evals" / "agents-md" / "ask-first" / "evals.json",
            ]
            for t in targets:
                t.parent.mkdir(parents=True, exist_ok=True)
                t.write_text("{}")
            (root / "skills" / "issue-tracker" / "SKILL.md").write_text("x")
            found = runner.discover_eval_files(root)
            self.assertEqual(sorted(found), sorted(targets))

    def test_empty_when_none_present(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(runner.discover_eval_files(Path(d)), [])


class RenderTranscript(unittest.TestCase):
    def test_renders_text_tool_call_and_result(self):
        lines = [
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Let me check."},
                {"type": "tool_use", "name": "Read", "input": {"file_path": "a.py"}},
            ]}}),
            json.dumps({"type": "user", "message": {"content": [
                {"type": "tool_result", "content": "file body"},
            ]}}),
            "not json — skip me",
            "",
        ]
        out = runner.render_transcript(lines)
        self.assertIn("## Assistant", out)
        self.assertIn("Let me check.", out)
        self.assertIn("Tool call: Read", out)
        self.assertIn("file_path", out)
        self.assertIn("Tool result", out)
        self.assertIn("file body", out)

    def test_tool_result_list_content(self):
        lines = [json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "content": [{"type": "text", "text": "hello"}]},
        ]}})]
        self.assertIn("hello", runner.render_transcript(lines))


class ParseGrading(unittest.TestCase):
    def test_raw_json(self):
        self.assertEqual(runner.parse_grading('{"a": 1}'), {"a": 1})

    def test_fenced_json(self):
        text = "Here it is:\n```json\n{\"summary\": {\"pass_rate\": 1.0}}\n```\n"
        self.assertEqual(runner.parse_grading(text)["summary"]["pass_rate"], 1.0)

    def test_prose_wrapped_json(self):
        text = 'Result: {"summary": {"pass_rate": 0.5}} done.'
        self.assertEqual(runner.parse_grading(text)["summary"]["pass_rate"], 0.5)

    def test_no_json_raises(self):
        with self.assertRaises(ValueError):
            runner.parse_grading("no json here")


class BuildGraderPrompt(unittest.TestCase):
    def test_embeds_parts_and_directive(self):
        out = runner.build_grader_prompt("GRADER RULES", ["exp A", "exp B"],
                                         "TRANSCRIPT BODY")
        self.assertIn("GRADER RULES", out)
        self.assertIn("exp A", out)
        self.assertIn("TRANSCRIPT BODY", out)
        self.assertIn("ONLY the grading JSON", out)


class CasePassed(unittest.TestCase):
    def test_threshold(self):
        self.assertTrue(runner.case_passed({"pass_rate": 1.0, "error": None}, 1.0))
        self.assertFalse(runner.case_passed({"pass_rate": 0.9, "error": None}, 1.0))
        self.assertTrue(runner.case_passed({"pass_rate": 0.8, "error": None}, 0.8))

    def test_error_never_passes(self):
        self.assertFalse(
            runner.case_passed({"pass_rate": 1.0, "error": "boom"}, 1.0))


class RunCase(unittest.TestCase):
    def setUp(self):
        self.workdir = Path(tempfile.mkdtemp(prefix="rc-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.workdir,
                                                            ignore_errors=True))
        self.case = {"id": 7, "prompt": "do the thing", "expectations": ["x"]}

    def test_success_returns_pass_rate(self):
        with mock.patch.object(runner, "run_executor", return_value="T"), \
             mock.patch.object(runner, "run_grader", return_value=_grading(1.0)):
            res = runner.run_case(self.case, "G", self.workdir, None, 10, 10)
        self.assertEqual(res["id"], 7)
        self.assertEqual(res["pass_rate"], 1.0)
        self.assertIsNone(res["error"])

    def test_executor_failure_is_captured(self):
        import subprocess
        with mock.patch.object(runner, "run_executor",
                               side_effect=subprocess.TimeoutExpired("claude", 1)):
            res = runner.run_case(self.case, "G", self.workdir, None, 10, 10)
        self.assertIn("executor failed", res["error"])
        self.assertEqual(res["pass_rate"], 0.0)

    def test_grader_failure_is_captured(self):
        with mock.patch.object(runner, "run_executor", return_value="T"), \
             mock.patch.object(runner, "run_grader",
                               side_effect=ValueError("bad json")):
            res = runner.run_case(self.case, "G", self.workdir, None, 10, 10)
        self.assertIn("grader failed", res["error"])


class RunSuiteAndMain(unittest.TestCase):
    @contextmanager
    def _fake_sandbox(self, _root):
        d = Path(tempfile.mkdtemp(prefix="sbx-"))
        try:
            yield d
        finally:
            __import__("shutil").rmtree(d, ignore_errors=True)

    def _write_eval(self, root: Path, pass_rates):
        path = root / "skills" / "s" / "evals" / "evals.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        evals = [{"id": i, "prompt": f"p{i}", "expectations": []}
                 for i, _ in enumerate(pass_rates)]
        path.write_text(json.dumps({"skill_name": "s", "evals": evals}))
        return path

    def test_suite_exit_zero_when_all_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = self._write_eval(root, [1.0, 1.0])
            grader = root / "grader.md"
            grader.write_text("RULES")
            with mock.patch.object(runner, "repo_root", return_value=root), \
                 mock.patch.object(runner, "make_sandbox", self._fake_sandbox), \
                 mock.patch.object(runner, "run_executor", return_value="T"), \
                 mock.patch.object(runner, "run_grader", return_value=_grading(1.0)):
                rc = runner.main(["--eval-file", str(path),
                                  "--grader-prompt", str(grader)])
            self.assertEqual(rc, 0)

    def test_suite_exit_one_when_a_case_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = self._write_eval(root, [1.0, 0.5])
            grader = root / "grader.md"
            grader.write_text("RULES")
            gradings = [_grading(1.0), _grading(0.5)]
            with mock.patch.object(runner, "repo_root", return_value=root), \
                 mock.patch.object(runner, "make_sandbox", self._fake_sandbox), \
                 mock.patch.object(runner, "run_executor", return_value="T"), \
                 mock.patch.object(runner, "run_grader", side_effect=gradings):
                rc = runner.main(["--eval-file", str(path),
                                  "--grader-prompt", str(grader)])
            self.assertEqual(rc, 1)

    def test_missing_grader_prompt_is_usage_error(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = self._write_eval(root, [1.0])
            with mock.patch.object(runner, "repo_root", return_value=root):
                rc = runner.main(["--eval-file", str(path),
                                  "--grader-prompt", str(root / "nope.md")])
            self.assertEqual(rc, 2)

    def test_no_eval_files_is_noop_success(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with mock.patch.object(runner, "repo_root", return_value=root):
                rc = runner.main([])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
