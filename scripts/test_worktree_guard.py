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
import os
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

# Every env var that marks a cloud (remote) session, mirrored from the guard so
# the two never drift. Stripped to build a deterministic *local* environment for
# the CLI tests below: otherwise, when this suite itself runs inside a cloud
# session (where these are set), the guard would no-op and every local-behaviour
# assertion would spuriously "pass" as allowed.
REMOTE_ENV_VARS = frozenset({guard.REMOTE_FLAG_ENV_VAR, *guard.REMOTE_MARKER_ENV_VARS})


def local_env(**overrides):
    """os.environ with every remote-session marker removed, plus any overrides."""
    env = {k: v for k, v in os.environ.items() if k not in REMOTE_ENV_VARS}
    env.update(overrides)
    return env


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


class IsRemoteSession(unittest.TestCase):
    def test_flag_true_is_remote(self):
        self.assertTrue(guard.is_remote_session({"CLAUDE_CODE_REMOTE": "true"}))

    def test_empty_env_is_local(self):
        self.assertFalse(guard.is_remote_session({}))

    def test_flag_other_than_true_alone_is_local(self):
        # The exact-"true" match is preserved for CLAUDE_CODE_REMOTE itself, so a
        # stray "1"/"false" with no other marker stays local.
        self.assertFalse(guard.is_remote_session({"CLAUDE_CODE_REMOTE": "1"}))

    def test_session_id_marker_is_remote(self):
        self.assertTrue(guard.is_remote_session(
            {"CLAUDE_CODE_REMOTE_SESSION_ID": "cse_x"}))

    def test_environment_type_marker_is_remote(self):
        self.assertTrue(guard.is_remote_session(
            {"CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE": "cloud_default"}))

    def test_empty_marker_values_are_local(self):
        # A marker present but empty is not a real remote session.
        self.assertFalse(guard.is_remote_session({
            "CLAUDE_CODE_REMOTE_SESSION_ID": "",
            "CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE": "",
        }))


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

    def test_merge_conflicted_file_allowed_despite_many_dirty(self):
        # A real merge dirties several conflicted files at once; editing one of
        # them to resolve the conflict must be allowed even though it is not the
        # only dirty file.
        allowed, reason = guard.evaluate_direct_edit(
            {"a.py", "b.py", "c.py"},
            "a.py",
            merge_conflict_files={"a.py", "b.py"},
        )
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_non_conflicted_file_still_blocked_during_merge(self):
        # A file Git does not list as conflicted stays subject to the normal
        # rule, even while a merge is in progress.
        allowed, reason = guard.evaluate_direct_edit(
            {"a.py", "b.py", "unrelated.py"},
            "unrelated.py",
            merge_conflict_files={"a.py", "b.py"},
        )
        self.assertFalse(allowed)
        self.assertIn("unrelated.py", reason)

    def test_no_merge_leaves_behavior_unchanged(self):
        # Empty conflict set (no merge) — identical to the plain single-code-file
        # case, which stays blocked.
        allowed, _ = guard.evaluate_direct_edit(
            set(), "src/main.py", merge_conflict_files=frozenset()
        )
        self.assertFalse(allowed)


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
        if env is None:
            # Default to a *local* environment: strip every remote marker so the
            # local-behaviour tests below stay deterministic even when the suite
            # itself runs inside a cloud session (where the guard no-ops). Cloud
            # behaviour is covered by the dedicated tests that set them explicitly.
            env = local_env()
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

    def test_unstaged_modification_parsed_with_full_path(self):
        # `git status --porcelain` prints an unstaged modification as ` M file`
        # (leading space). Regression guard: the leading space must survive so
        # the fixed-column `line[3:]` slice yields the full path, not a
        # first-character-truncated phantom like `EADME.md`.
        (self.repo / "README.md").write_text("changed\n")
        self.assertEqual(guard._dirty_files(str(self.repo)), {"README.md"})

    def test_lone_unstaged_doc_modification_allowed(self):
        # Reproduction case: a single unstaged-modified doc file as the only
        # dirty entry, edited again. Before the fix the truncated phantom path
        # made the guard count it twice and deny this trivial edit.
        (self.repo / "README.md").write_text("changed\n")
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

    def test_remote_session_allows_direct_code_edit(self):
        # Cloud sessions run in their own clone, so the guard no-ops: a direct
        # code edit in the main checkout that would be denied locally is allowed.
        env = local_env(CLAUDE_CODE_REMOTE="true")
        result = self._run("Write", str(self.repo / "src.py"), env=env)
        self._assert_allowed(result)

    def test_remote_session_allows_edit_on_protected_branch(self):
        # The remote no-op is total: even the protected-branch check is skipped,
        # since there is no shared checkout to protect in a per-session clone.
        self._git("branch", "-m", "main")
        env = local_env(CLAUDE_CODE_REMOTE="true")
        result = self._run("Edit", str(self.repo / "README.md"), env=env)
        self._assert_allowed(result)

    def test_remote_flag_other_than_true_still_enforced(self):
        # A non-"true" CLAUDE_CODE_REMOTE value, with no other remote marker
        # present, does not disable the guard: local enforcement stays intact.
        env = local_env(CLAUDE_CODE_REMOTE="1")
        result = self._run("Write", str(self.repo / "src.py"), env=env)
        self._assert_denied(result)

    def test_remote_session_id_marker_allows_direct_code_edit(self):
        # Regression for the guard firing in cloud sessions: the flag need not be
        # "true" — a CLAUDE_CODE_REMOTE_SESSION_ID set by the remote runner is on
        # its own enough to recognize the per-session clone and no-op.
        env = local_env(CLAUDE_CODE_REMOTE_SESSION_ID="cse_test")
        result = self._run("Write", str(self.repo / "src.py"), env=env)
        self._assert_allowed(result)

    def test_remote_environment_type_marker_allows_direct_code_edit(self):
        # Likewise, CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE alone marks a cloud
        # session, even without CLAUDE_CODE_REMOTE=="true".
        env = local_env(CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE="cloud_default")
        result = self._run("Write", str(self.repo / "src.py"), env=env)
        self._assert_allowed(result)

    def _start_merge_conflict(self):
        """Leave the repo mid-merge with `conflict.py` unmerged."""
        (self.repo / "conflict.py").write_text("base\n")
        self._git("add", "conflict.py")
        self._git("commit", "-q", "-m", "base")
        self._git("checkout", "-q", "-b", "child-a")
        (self.repo / "conflict.py").write_text("a\n")
        self._git("commit", "-qam", "a")
        self._git("checkout", "-q", "issue/demo")
        self._git("checkout", "-q", "-b", "child-b")
        (self.repo / "conflict.py").write_text("b\n")
        self._git("commit", "-qam", "b")
        self._git("checkout", "-q", "issue/demo")
        self._git("merge", "-q", "child-a")
        # This merge conflicts; it must NOT use check=True.
        merge = subprocess.run(
            ["git", "merge", "child-b"], cwd=self.repo,
            capture_output=True, text=True,
        )
        self.assertNotEqual(merge.returncode, 0, "expected a merge conflict")

    def test_conflicted_file_editable_during_merge(self):
        self._start_merge_conflict()
        result = self._run("Edit", str(self.repo / "conflict.py"))
        self._assert_allowed(result)

    def test_unrelated_file_still_blocked_during_merge(self):
        self._start_merge_conflict()
        # A brand-new code file, not part of the conflict, stays blocked.
        result = self._run("Write", str(self.repo / "unrelated.py"))
        reason = self._assert_denied(result)
        self.assertIn("unrelated.py", reason)

    def test_malformed_stdin_allows(self):
        result = subprocess.run(
            [sys.executable, MODULE_PATH], cwd=self.repo,
            input="not json", capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


REPO_ROOT = Path(__file__).resolve().parent.parent


@unittest.skipIf(shutil.which("git") is None, "git not available")
class BypassMarkerIgnored(unittest.TestCase):
    """The bypass marker disables the guard for a whole session; committed, it
    would disable it for the whole repo. So it must be git-ignored here, and the
    cloud-session-bootstrap skill installs the same entry into target repos."""

    def test_this_repo_ignores_the_bypass_marker(self):
        result = subprocess.run(
            ["git", "check-ignore", ".claude/.worktree-bypass"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            ".claude/.worktree-bypass is not git-ignored — a `git add -A` "
            "could commit it and disable the guard permanently",
        )
        self.assertEqual(result.stdout.strip(), ".claude/.worktree-bypass")


if __name__ == "__main__":
    unittest.main(verbosity=2)
