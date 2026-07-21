#!/usr/bin/env python3
"""Integration test for
skills/cloud-session-bootstrap/assets/worktree-create.sh.

Drives the WorktreeCreate hook script over stdin/stdout against a throwaway
git repo and asserts a native worktree request lands under `.worktrees/<name>`
— the redirect AGENTS.md's "Worktree Isolation" rule promises for every
repo this skill sets up.

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
        self.tmp = Path(tempfile.mkdtemp())
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

    def _git(self, *args):
        subprocess.run(
            ["git", *args], cwd=self.repo, check=True,
            capture_output=True, text=True,
        )

    def _run(self, worktree_name, base_ref, cwd=None):
        payload = {"worktree_name": worktree_name, "base_ref": base_ref}
        return subprocess.run(
            ["bash", str(SCRIPT)], cwd=cwd or self.repo,
            input=json.dumps(payload), capture_output=True, text=True,
        )

    def test_native_worktree_lands_under_dot_worktrees(self):
        result = self._run("agent-42", "HEAD")
        self.assertEqual(result.returncode, 0, result.stderr)

        printed = result.stdout.strip()
        expected = self.repo / ".worktrees" / "agent-42"
        # The script must print exactly the created path, and nothing else.
        self.assertEqual(printed, str(expected))
        self.assertTrue(expected.is_dir(), "worktree directory was not created")

        # And git must actually register it there, not under .claude/worktrees/.
        listing = subprocess.run(
            ["git", "worktree", "list"], cwd=self.repo,
            capture_output=True, text=True,
        ).stdout
        self.assertIn(str(expected), listing)
        self.assertNotIn(".claude/worktrees", listing)

    def test_stays_flat_when_invoked_from_a_linked_worktree(self):
        # Invoked with cwd inside a linked worktree, the redirect must still
        # target the MAIN checkout's .worktrees/, never nest a second
        # .worktrees/ under the linked worktree (AGENTS.md: register every
        # worktree flat against the shared .git).
        first = self._run("child-a", "HEAD")
        self.assertEqual(first.returncode, 0, first.stderr)
        linked = self.repo / ".worktrees" / "child-a"

        second = self._run("child-b", "HEAD", cwd=linked)
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
        self.assertEqual(self._run("dup", "HEAD").returncode, 0)
        self.assertNotEqual(self._run("dup", "HEAD").returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
