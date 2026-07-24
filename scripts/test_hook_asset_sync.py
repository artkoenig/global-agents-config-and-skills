#!/usr/bin/env python3
"""Guard against hook-definition drift inside this config repo.

The cloud-session-bootstrap skill installs its hook scripts into a target
project by copying them from `skills/cloud-session-bootstrap/assets/`. This
repo dogfoods the same hooks in its own `.claude/hooks/`. To keep a single
source of truth — and satisfy issue 05/01's "the hook definition must not exist
as a second, independently maintainable copy" — this repo's copies must stay
byte-identical to the assets, and `.claude/settings.json` must reference the
scripts by path rather than inlining their logic as a drifting `bash -c '…'`
blob.

Run: python3 scripts/test_hook_asset_sync.py
  or python3 -m unittest -v (from the scripts/ directory)
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
ASSET_DIR = REPO_ROOT / "skills" / "cloud-session-bootstrap" / "assets"
HOOK_DIR = REPO_ROOT / ".claude" / "hooks"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"

# Bind the two modules that each keep a hand-maintained copy of the same
# constant(s): the authoritative rules module and the deliberately
# self-contained guard asset. Imported the same way the dedicated per-module
# tests import them (scripts/ and the asset dir on sys.path); this test only
# reads their constants, never their behaviour.
sys.path.insert(0, str(ASSET_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

import git_workflow_rules as rules  # noqa: E402
import worktree_guard as guard  # noqa: E402

# Hooks this config repo dogfoods in its own `.claude/hooks/` must match the
# skill's canonical asset byte-for-byte, so re-running the skill would detect no
# drift. `session-start.sh` is included too: this repo now installs it so its own
# cloud sessions load the personal skills/subagents (the hook is a no-op locally,
# guarding on CLAUDE_CODE_REMOTE), so its copy must stay in sync like the others.
SYNCED_HOOKS = ("worktree_guard.py", "worktree-create.sh", "session-start.sh")


class HookCopiesMatchAssets(unittest.TestCase):
    def test_byte_identical_to_assets(self):
        for name in SYNCED_HOOKS:
            with self.subTest(hook=name):
                asset = ASSET_DIR / name
                installed = HOOK_DIR / name
                self.assertTrue(asset.is_file(), f"missing asset {asset}")
                self.assertTrue(installed.is_file(), f"missing hook {installed}")
                self.assertEqual(
                    installed.read_bytes(), asset.read_bytes(),
                    f"{installed} has drifted from {asset}; re-copy the asset",
                )


class SettingsReferenceScriptsByPath(unittest.TestCase):
    def setUp(self):
        self.hooks = json.loads(SETTINGS.read_text())["hooks"]

    def _commands(self, event):
        return [
            h["command"]
            for entry in self.hooks.get(event, [])
            for h in entry.get("hooks", [])
        ]

    def test_worktree_create_calls_the_script(self):
        cmds = self._commands("WorktreeCreate")
        self.assertTrue(cmds, "no WorktreeCreate hook wired in settings.json")
        for cmd in cmds:
            # Reference the script by path — never re-inline `git worktree add`,
            # which would be a second copy that drifts from the asset.
            self.assertIn("worktree-create.sh", cmd)
            self.assertNotIn("git worktree add", cmd)

    def test_pretooluse_calls_the_guard(self):
        cmds = self._commands("PreToolUse")
        self.assertTrue(any("worktree_guard.py" in c for c in cmds),
                        "PreToolUse does not wire worktree_guard.py")


# Constants that git_workflow_rules.py (authoritative) and the self-contained
# worktree_guard.py asset each define independently and must keep identical by
# hand. A cross-repo import is impossible on purpose (the guard is copied into
# foreign repos with no access to this checkout), so nothing but this test binds
# the copies together. Each entry maps a human label to the two frozensets that
# must stay equal.
#
# The guard additionally defines CHECKED_TOOLS, DEFAULT_ISSUE_TRACKER_DIR and
# BYPASS_MARKER_RELPATH, but those have no counterpart in the rules module —
# they are guard-only, not hand-synced pairs — so the only shared constants are
# the two below.
HAND_SYNCED_CONSTANTS = (
    ("trivial file extensions", rules.TRIVIAL_EXTENSIONS, guard.TRIVIAL_EXTENSIONS),
    ("protected branches", rules.PROTECTED_REFS, guard.PROTECTED_BRANCHES),
)


class HandSyncedConstantsAgree(unittest.TestCase):
    def test_copies_are_identical(self):
        for label, authoritative, copy in HAND_SYNCED_CONSTANTS:
            with self.subTest(constant=label):
                self.assertEqual(
                    authoritative, copy,
                    f"{label} have drifted between git_workflow_rules.py and "
                    "worktree_guard.py; the pre-edit guard and the pre-push hook "
                    "would classify changes differently — re-sync the copies",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
