#!/usr/bin/env python3
"""Integration test for
skills/cloud-session-bootstrap/assets/worktree-create.sh.

Drives the WorktreeCreate hook script over stdin/stdout against a throwaway
git repo, using the input JSON documented at
https://code.claude.com/docs/en/hooks.md ("WorktreeCreate input"): the only
worktree-specific field is `name` — there is no base-ref field, so the hook
must branch from HEAD on its own. Asserts a native worktree request lands
under `.worktrees/<name>` — the redirect AGENTS.md's "Worktree Isolation"
rule promises for every repo this skill sets up.

Run: python3 scripts/test_worktree_create.py
  or python3 -m unittest -v (from the scripts/ directory)
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (
    REPO_ROOT
    / "skills" / "cloud-session-bootstrap" / "assets" / "worktree-create.sh"
)


@unittest.skipUnless(shutil.which("jq"), "jq is required by worktree-create.sh")
class WorktreeCreateRedirect(unittest.TestCase):
    def setUp(self):
        # resolve(): git prints fully resolved paths, and macOS's /tmp is a
        # symlink into /private — unresolved, every path comparison would fail.
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "t@t.t")
        self._git("config", "user.name", "t")
        (self.repo / "README.md").write_text("x\n")
        self._git("add", "README.md")
        self._git("commit", "-qm", "init")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _git(self, *args, cwd=None):
        return subprocess.run(
            ["git", *args], cwd=cwd or self.repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def _run(self, payload, cwd=None):
        return subprocess.run(
            ["bash", str(SCRIPT)], cwd=cwd or self.repo,
            input=json.dumps(payload), capture_output=True, text=True,
        )

    @staticmethod
    def _documented_input(name):
        # The full documented input shape; extra common fields must be ignored.
        return {
            "session_id": "abc123",
            "cwd": "/wherever",
            "hook_event_name": "WorktreeCreate",
            "name": name,
        }

    def test_native_worktree_lands_under_dot_worktrees(self):
        result = self._run(self._documented_input("agent-42"))
        self.assertEqual(result.returncode, 0, result.stderr)

        expected = self.repo / ".worktrees" / "agent-42"
        # The created path must be the last non-empty stdout line — the value
        # Claude Code reads as the worktree path.
        last_line = [l for l in result.stdout.splitlines() if l.strip()][-1]
        self.assertEqual(last_line, str(expected))
        self.assertTrue(expected.is_dir(), "worktree directory was not created")

        # And git must actually register it there, not under .claude/worktrees/.
        listing = self._git("worktree", "list")
        self.assertIn(str(expected), listing)
        self.assertNotIn(".claude/worktrees", listing)

    def test_branches_from_the_invoking_checkouts_head(self):
        # No base ref arrives on stdin, so the hook itself must branch from
        # HEAD — AGENTS.md's "head" semantics. Add a second commit first so
        # HEAD is distinguishable from the initial default-branch state.
        (self.repo / "work.md").write_text("in progress\n")
        self._git("add", "work.md")
        self._git("commit", "-qm", "work")
        head = self._git("rev-parse", "HEAD")

        result = self._run(self._documented_input("agent-head"))
        self.assertEqual(result.returncode, 0, result.stderr)
        worktree_head = self._git(
            "rev-parse", "HEAD", cwd=self.repo / ".worktrees" / "agent-head"
        )
        self.assertEqual(worktree_head, head)

    def test_stays_flat_when_invoked_from_a_linked_worktree(self):
        # Invoked with cwd inside a linked worktree, the redirect must still
        # target the MAIN checkout's .worktrees/, never nest a second
        # .worktrees/ under the linked worktree (AGENTS.md: register every
        # worktree flat against the shared .git).
        first = self._run(self._documented_input("child-a"))
        self.assertEqual(first.returncode, 0, first.stderr)
        linked = self.repo / ".worktrees" / "child-a"

        second = self._run(self._documented_input("child-b"), cwd=linked)
        self.assertEqual(second.returncode, 0, second.stderr)
        expected = self.repo / ".worktrees" / "child-b"
        self.assertEqual(second.stdout.strip(), str(expected))
        self.assertFalse(
            (linked / ".worktrees").exists(),
            "worktree nested under the linked worktree instead of staying flat",
        )

    def test_nonzero_exit_on_duplicate(self):
        # A second create at the same path must fail (non-zero), so Claude Code
        # fails worktree creation rather than silently proceeding.
        self.assertEqual(
            self._run(self._documented_input("dup")).returncode, 0
        )
        self.assertNotEqual(
            self._run(self._documented_input("dup")).returncode, 0
        )

    def test_missing_name_fails_loudly(self):
        # A payload without `name` must abort with a non-zero exit instead of
        # creating a worktree literally called "null" from a "null" ref — the
        # exact failure that broke cloud session starts (issue 05/03).
        result = self._run({"hook_event_name": "WorktreeCreate"})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo / ".worktrees" / "null").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
