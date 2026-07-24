#!/usr/bin/env python3
"""Unit tests for scripts/git_workflow_rules.py.

Two layers:
  - Exhaustive tests of the pure predicates (no git, no I/O).
  - A lightweight integration test that drives the `pre-push` CLI against a
    throwaway git repo, exercising the git plumbing and stdin wiring end to end.

Run: python3 scripts/test_git_workflow_rules.py
  or python3 -m unittest -v (from the scripts/ directory)
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import git_workflow_rules as rules  # noqa: E402

MODULE_PATH = str(Path(__file__).resolve().parent / "git_workflow_rules.py")
ZERO_SHA = "0" * 40


class IsProtectedRef(unittest.TestCase):
    def test_protected(self):
        for ref in ("main", "master", "refs/heads/main", "refs/heads/master"):
            with self.subTest(ref=ref):
                self.assertTrue(rules.is_protected_ref(ref))

    def test_not_protected(self):
        for ref in ("issue/foo", "refs/heads/issue/foo", "develop",
                    "refs/heads/develop", "refs/tags/main", "mainline",
                    "refs/heads/main-thing"):
            with self.subTest(ref=ref):
                self.assertFalse(rules.is_protected_ref(ref))


class CommitHasAgentCoauthor(unittest.TestCase):
    def test_detects_trailer(self):
        for msg in (
            "Fix bug\n\nCo-authored-by: A B <a@b.com>",
            "Fix bug\n\nCo-Authored-By: A B <a@b.com>",
            "Fix bug\n\nco-authored-by: A B <a@b.com>",
            "Subject\n\nSigned-off-by: X <x@y>\nCo-authored-by: A B <a@b.com>",
            "Subject\n\n  Co-authored-by: A B <a@b.com>",
            "Co-authored-by: A B <a@b.com>",
        ):
            with self.subTest(msg=msg):
                self.assertTrue(rules.commit_has_agent_coauthor(msg))

    def test_ignores_non_trailers(self):
        for msg in (
            "Fix bug",
            "Fix bug\n\nSigned-off-by: X <x@y>",
            "Discuss how co-authored-by trailers work in the body",
            "Co-authored-by:",          # empty value
            "Co-authored-by:   ",       # only whitespace value
            "prefix Co-authored-by: A B <a@b>",  # not at line start
        ):
            with self.subTest(msg=msg):
                self.assertFalse(rules.commit_has_agent_coauthor(msg))


class IsTrivialChange(unittest.TestCase):
    def test_single_file_small_diff(self):
        self.assertTrue(rules.is_trivial_change(["a.py"], 1))
        self.assertTrue(rules.is_trivial_change(["a.py"], 0))

    def test_single_file_docs_config_extension_any_size(self):
        for f in ("README.md", "data.json", "c.yaml", "c.yml", "notes.txt",
                  "UPPER.MD"):
            with self.subTest(f=f):
                self.assertTrue(rules.is_trivial_change([f], 999))

    def test_single_code_file_large_diff_is_not_trivial(self):
        self.assertFalse(rules.is_trivial_change(["a.py"], 2))
        self.assertFalse(rules.is_trivial_change(["src/main.rs"], 50))

    def test_multiple_files_never_trivial(self):
        self.assertFalse(rules.is_trivial_change(["a.md", "b.md"], 1))
        self.assertFalse(rules.is_trivial_change(["a.py", "b.py"], 0))

    def test_no_files_is_not_trivial(self):
        self.assertFalse(rules.is_trivial_change([], 0))


class Helpers(unittest.TestCase):
    def test_strip_heads(self):
        self.assertEqual(rules._strip_heads("refs/heads/issue/foo"), "issue/foo")
        self.assertEqual(rules._strip_heads("refs/heads/main"), "main")
        self.assertEqual(rules._strip_heads("issue/foo"), "issue/foo")
        self.assertEqual(rules._strip_heads("refs/tags/v1"), "refs/tags/v1")

    def test_is_zero_sha(self):
        self.assertTrue(rules._is_zero_sha(ZERO_SHA))
        self.assertTrue(rules._is_zero_sha("0000000"))
        self.assertFalse(rules._is_zero_sha("abc123"))
        self.assertFalse(rules._is_zero_sha(""))


@unittest.skipIf(shutil.which("git") is None, "git not available")
class PrePushCli(unittest.TestCase):
    """Drive the CLI against a throwaway repo to cover git plumbing + stdin."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="gwr-test-"))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self._git("init", "-q", "-b", "issue/foo")
        self._git("config", "user.name", "Test")
        self._git("config", "user.email", "test@example.com")

    def _git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True,
                       capture_output=True, text=True)

    def _commit(self, message):
        (self.repo / "file.txt").write_text("x\n")
        self._git("add", "file.txt")
        self._git("commit", "-q", "-m", message)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def _run_pre_push(self, stdin_text):
        env = dict(os.environ)
        return subprocess.run(
            [sys.executable, MODULE_PATH, "pre-push", "origin", "url"],
            cwd=self.repo, input=stdin_text, capture_output=True, text=True,
            env=env,
        )

    def test_clean_new_branch_passes(self):
        sha = self._commit("Add file")
        line = f"refs/heads/issue/foo {sha} refs/heads/issue/foo {ZERO_SHA}\n"
        result = self._run_pre_push(line)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_coauthor_commit_is_rejected(self):
        sha = self._commit("Add file\n\nCo-authored-by: A B <a@b.com>")
        line = f"refs/heads/issue/foo {sha} refs/heads/issue/foo {ZERO_SHA}\n"
        result = self._run_pre_push(line)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Co-authored-by", result.stderr)

    def test_push_to_main_is_rejected(self):
        sha = self._commit("Add file")
        line = f"refs/heads/issue/foo {sha} refs/heads/main {ZERO_SHA}\n"
        result = self._run_pre_push(line)
        self.assertEqual(result.returncode, 1)
        self.assertIn("protected", result.stderr)

    def test_non_issue_branch_name_is_accepted(self):
        # Branch names are no longer enforced: a cloud session's
        # platform-assigned branch (e.g. claude/...) must push cleanly rather
        # than be rejected, since the session cannot rename it.
        self._git("branch", "-m", "claude/some-task")
        sha = self._commit("Add file")
        line = f"refs/heads/claude/some-task {sha} refs/heads/claude/some-task {ZERO_SHA}\n"
        result = self._run_pre_push(line)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_stdin_passes(self):
        self._commit("Add file")
        result = self._run_pre_push("")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_branch_deletion_line_is_ignored(self):
        self._commit("Add file")
        line = f"(delete) {ZERO_SHA} refs/heads/issue/foo {ZERO_SHA}\n"
        result = self._run_pre_push(line)
        self.assertEqual(result.returncode, 0, result.stderr)


HOOK_PATH = Path(__file__).resolve().parent.parent / ".githooks" / "pre-push"


@unittest.skipIf(shutil.which("git") is None, "git not available")
@unittest.skipUnless(HOOK_PATH.exists(), ".githooks/pre-push not present")
class CentralHookDeployment(unittest.TestCase):
    """The hook lives in this config repo but must work when a *foreign* repo
    points core.hooksPath at it: the checker script is found relative to the
    hook ($0), while git state is read from the pushing repo (cwd)."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="gwr-central-"))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self._git("init", "-q", "-b", "issue/demo")
        self._git("config", "user.name", "Test")
        self._git("config", "user.email", "test@example.com")

    def _git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True,
                       capture_output=True, text=True)

    def _commit(self, message):
        (self.repo / "f.txt").write_text("x\n")
        self._git("add", "f.txt")
        self._git("commit", "-q", "-m", message)
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo,
                              check=True, capture_output=True,
                              text=True).stdout.strip()

    def _run_hook(self, stdin_text):
        # cwd is the foreign pushing repo; the hook is invoked by absolute path,
        # exactly as core.hooksPath -> <config-repo>/.githooks would.
        return subprocess.run(
            [str(HOOK_PATH), "origin", "url"], cwd=self.repo,
            input=stdin_text, capture_output=True, text=True,
        )

    def test_clean_push_passes(self):
        sha = self._commit("clean")
        line = f"refs/heads/issue/demo {sha} refs/heads/issue/demo {ZERO_SHA}\n"
        self.assertEqual(self._run_hook(line).returncode, 0)

    def test_coauthor_is_rejected(self):
        sha = self._commit("bad\n\nCo-authored-by: X <x@y>")
        line = f"refs/heads/issue/demo {sha} refs/heads/issue/demo {ZERO_SHA}\n"
        result = self._run_hook(line)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Co-authored-by", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
