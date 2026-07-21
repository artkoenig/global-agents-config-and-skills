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
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = REPO_ROOT / "skills" / "cloud-session-bootstrap" / "assets"
HOOK_DIR = REPO_ROOT / ".claude" / "hooks"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"

# Hooks this config repo dogfoods in its own `.claude/hooks/` must match the
# skill's canonical asset byte-for-byte, so re-running the skill would detect no
# drift. `session-start.sh` is deliberately absent: it clones this repo into a
# target, so this repo — being that source — has no reason to install it.
SYNCED_HOOKS = ("worktree_guard.py", "worktree-create.sh")


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
