---
name: cloud-session-bootstrap
description: Wires a project so that its Claude Code CLOUD sessions (Claude Code on the web / CLAUDE_CODE_REMOTE) load Artjom's personal skills and subagents from the global-agents-config-and-skills repo, by installing a SessionStart hook that clones that repo and symlinks its skills/ and agents/ into ~/.claude. Use this when setting up a new project for the first time, when a project's session-start hook is missing the agents/ symlinking step (skills only, no subagents), or when the hook has drifted from the canonical version. Trigger on phrases like "set up cloud sessions for this project", "wire up my skills here", "install the agent hook", "this project doesn't load my subagents in the cloud", or "init the personal-agents setup". Do not run this for every project reflexively — only for ones that should actually use this personal skill/agent set, and only when the user asks or clearly wants it for the current project.
user-invocable: true
---

# Cloud Session Bootstrap

There is no Claude Code plugin marketplace anymore for this personal
skill/agent set — it was retired in favor of a SessionStart hook that clones
[global-agents-config-and-skills](https://github.com/artkoenig/global-agents-config-and-skills)
directly into `~/.claude` on cloud (remote) session start. Locally, nothing
needs to run: `~/.claude/skills` and `~/.claude/agents` already symlink into a
local clone of that repo.

This skill installs that hook into a **target project** — a different
repository from this one. Only run it when the user actually wants this
project on the personal skill/agent set; do not apply it opportunistically to
every repository you touch.

## 1. Confirm the target and its git state

Follow AGENTS.md's git rules as usual: confirm the target project is a git
repository, print its current branch, and ask whether to use it or create a
new one. The files this skill writes (`.claude/hooks/session-start.sh`,
`.claude/settings.json`) are ordinary versioned project files.

## 2. Check what's already there

- `.claude/hooks/session-start.sh` — read it if present.
  - If it doesn't exist, you're installing fresh.
  - If it exists and is byte-identical to
    [assets/session-start.sh](assets/session-start.sh), it's already
    up to date — report that and stop; there's nothing to do.
  - If it exists but differs, diff the two. A missing agents-symlinking step
    (an older version only handles `skills/`) is the expected drift and safe
    to update. Anything else — custom logic someone added on top — must not be
    silently overwritten: show the user the diff and ask before replacing it.
- `.claude/settings.json` — read it if present. Note whether it already wires a
  `SessionStart` hook.
- `.claude/settings.json` / `.claude/settings.local.json` — check for
  leftover references to the retired marketplace (`enabledPlugins` or
  `extraKnownMarketplaces` mentioning `artkoenig`). If found, point them out
  and ask whether to remove them; don't remove silently, since they may be
  intentional in a project you don't have full context on.

## 3. Install the hook script

Copy [assets/session-start.sh](assets/session-start.sh) to
`.claude/hooks/session-start.sh` in the target project, verbatim — it is
already generic (it only hardcodes the agents repo's public clone URL, which
is the same for every project). Make it executable (`chmod +x`).

Do not paraphrase or hand-retype the script. Copy the file as-is, so future
re-runs of this skill can diff byte-for-byte and detect drift reliably.

## 4. Wire `.claude/settings.json`

Ensure the target's `.claude/settings.json` contains a `SessionStart` hook
entry invoking the script:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

- If `.claude/settings.json` doesn't exist, create it with just this content.
- If it exists, merge: add this hook entry into the `hooks.SessionStart` array
  without disturbing any other hooks or settings already there. If an entry
  with this exact command already exists, leave it alone.

## 5. Report

Tell the user:

- What was installed or updated, and what was left untouched.
- That this only changes **cloud/remote** sessions
  (`CLAUDE_CODE_REMOTE=true`) — local sessions in this project are unaffected.
- That the target environment needs GitHub access to
  `global-agents-config-and-skills` to clone it (it's a private repo), the same
  access it uses to clone the project itself.
- That the new/changed files (`.claude/hooks/session-start.sh`,
  `.claude/settings.json`) still need to be committed — per AGENTS.md's git
  rules, don't commit them yourself unless asked.
