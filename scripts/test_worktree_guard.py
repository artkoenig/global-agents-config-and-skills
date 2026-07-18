#!/usr/bin/env python3
"""Unit tests for skills/cloud-session-bootstrap/assets/worktree_guard.py.

Two layers, same split as test_git_workflow_rules.py:
  - Exhaustive tests of the pure predicates (no git, no I/O).
  - An integration test that drives the PreToolUse CLI over stdin/stdout
    against a throwaway git repo, exercising the git plumbing.

Run: python3 scripts/test_worktree_guard.py
  or python3 -m unittest -v (from the scripts/ directory)
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ASSET_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills" / "cloud-session-bootstrap" / "assets"
)
sys.path.insert(0, str(ASSET_DIR))

import worktree_guard as guard  # noqa: E402

MODULE_PATH = str(ASSET_DIR / "worktree_guard.py")


class IsIssueTrackerPath(unittest.TestCase):
    def test_matches_default_dir(self):
        self.assertTrue(guard.is_issue_tracker_path(
            "docs/issues/01-foo/issue.md", "docs/issues"))

    def test_rejects_other_paths(self):
        self.assertFalse(guard.is_issue_tracker_path("src/main.py", "docs/issues"))
        self.assertFalse(guard.is_issue_tracker_path("docs/README.md", "docs/issues"))

    def test_custom_dir(self):
        self.assertTrue(guard.is_issue_tracker_path("tickets/01/issue.md", "tickets"))
        self.assertFalse(guard.is_issue_tracker_path("docs/issues/01/issue.md", "tickets"))


class IsProtectedBranch(unittest.TestCase):
    def test_protected(self):
        for b in ("main", "master"):
            with self.subTest(b=b):
                self.assertTrue(guard.is_protected_branch(b))

    def test_not_protected(self):
        for b in ("issue/foo", "work/anything", None, "mainline"):
            with self.subTest(b=b):
                self.assertFalse(guard.is_protected_branch(b))


class EvaluateDirectEdit(unittest.TestCase):
    def test_single_doc_file_allowed(self):
        allowed, reason = guard.evaluate_direct_edit(set(), "AGENTS.md")
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_single_code_file_blocked(self):
        allowed, reason = guard.evaluate_direct_edit(set(), "src/main.py")
        self.assertFalse(allowed)
        self.assertIn("main.py", reason)

    def test_second_file_blocked_even_if_doc(self):
        allowed, _ = guard.evaluate_direct_edit({"README.md"}, "AGENTS.md")
        self.assertFalse(allowed)

    def test_second_file_blocked_for_code(self):
        allowed, reason = guard.evaluate_direct_edit({"a.py"}, "b.py")
        self.assertFalse(allowed)
        self.assertIn("a.py", reason)

    def test_issue_tracker_path_always_allowed(self):
        allowed, reason = guard.evaluate_direct_edit(
            {"docs/issues/01-foo/issue.md", "docs/issues/01-foo/02-bar/issue.md"},
            "docs/issues/01-foo/03-baz/issue.md",
        )
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_dirty_issue_tracker_files_do_not_block_unrelated_trivial_edit(self):
        allowed, _ = guard.evaluate_direct_edit(
            {"docs/issues/01-foo/issue.md"}, "README.md"
        )
        self.assertTrue(allowed)

    def test_custom_issue_tracker_dir(self):
        allowed, _ = guard.evaluate_direct_edit(
            {"tickets/01/issue.md"}, "tickets/02/issue.md", issue_tracker_dir="tickets"
        )
        self.assertTrue(allowed)


@unittest.skipIf(shutil.which("git") is None, "git not available")
class PreToolUseCli(unittest.TestCase):
    """Drive the hook's stdin/stdout contract against a throwaway repo."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="wg-test-"))
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self._git("init", "-q", "-b", "issue/demo")
        self._git("config", "user.name", "Test")
        self._git("config", "user.email", "test@example.com")
        (self.repo / "README.md").write_text("hello\n")
        self._git("add", "README.md")
        self._git("commit", "-q", "-m", "init")

    def _git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True,
                       capture_output=True, text=True)

    def _run(self, tool_name, file_path, env=None):
        payload = {"tool_name": tool_name, "tool_input": {"file_path": file_path}}
        return subprocess.run(
            [sys.executable, MODULE_PATH], cwd=self.repo,
            input=json.dumps(payload), capture_output=True, text=True, env=env,
        )

    def _assert_allowed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def _assert_denied(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["hookSpecificOutput"]["permissionDecision"], "deny"
        )
        return payload["hookSpecificOutput"]["permissionDecisionReason"]

    def test_non_checked_tool_allowed(self):
        result = self._run("Bash", str(self.repo / "src.py"))
        self._assert_allowed(result)

    def test_clean_checkout_single_doc_edit_allowed(self):
        result = self._run("Edit", str(self.repo / "README.md"))
        self._assert_allowed(result)

    def test_clean_checkout_single_code_edit_denied(self):
        result = self._run("Write", str(self.repo / "src.py"))
        reason = self._assert_denied(result)
        self.assertIn("src.py", reason)

    def test_second_dirty_file_denied(self):
        (self.repo / "a.py").write_text("x\n")
        self._git("add", "a.py")
        result = self._run("Edit", str(self.repo / "b.py"))
        self._assert_denied(result)

    def test_issue_tracker_files_exempt_even_when_multiple(self):
        issues = self.repo / "docs" / "issues" / "01-foo"
        issues.mkdir(parents=True)
        (issues / "issue.md").write_text("x\n")
        self._git("add", "docs")
        result = self._run("Write", str(issues / "02-bar" / "issue.md"))
        self._assert_allowed(result)

    def test_editing_inside_worktree_allowed(self):
        wt = self.repo / ".worktrees" / "child"
        self._git("worktree", "add", str(wt), "-b", "work/child")
        result = self._run("Write", str(wt / "src.py"))
        self._assert_allowed(result)

    def test_protected_branch_denied_even_for_docs(self):
        self._git("branch", "-m", "main")
        result = self._run("Edit", str(self.repo / "README.md"))
        reason = self._assert_denied(result)
        self.assertIn("protected", reason)

    def test_bypass_marker_allows_everything(self):
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / ".worktree-bypass").touch()
        result = self._run("Write", str(self.repo / "src.py"))
        self._assert_allowed(result)

    def test_malformed_stdin_allows(self):
        result = subprocess.run(
            [sys.executable, MODULE_PATH], cwd=self.repo,
            input="not json", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
