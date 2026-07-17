---
name: cloud-session-bootstrap
description: Wires a project so that its Claude Code CLOUD sessions (Claude Code on the web / CLAUDE_CODE_REMOTE) load Artjom's personal skills and subagents from the global-agents-config-and-skills repo, by installing a SessionStart hook that clones that repo and symlinks its skills/ and agents/ into ~/.claude. Mandatory at the start of every session in every git repository, per AGENTS.md's Cloud Session Bootstrap Trigger — run it proactively whenever a project's hook is missing or has drifted, not only when asked. Also trigger on phrases like "set up cloud sessions for this project", "wire up my skills here", "install the agent hook", "this project doesn't load my subagents in the cloud", or "init the personal-agents setup".
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
repository from this one. Per AGENTS.md's Cloud Session Bootstrap Trigger,
run it at the start of every session in every git repository **Artjom owns**
where it isn't already installed and current — mandatory by default there,
not something to wait for the user to request. It does not apply to repos
he doesn't own; see step 1.

## 1. Confirm this is Artjom's repo

```bash
git remote get-url origin
```

- No remote configured (a fresh local repo, nothing pushed yet): treat it as
  his — proceed.
- Remote host is `github.com` and the owner/org segment of the path is
  `artkoenig`: proceed.
- Anything else (a different owner or org, e.g. a work, client, or
  open-source repo he's contributing to): **stop here, install nothing, and
  don't ask** — this skill is scoped to his own repos only.

## 2. Confirm the target and its git state

Follow AGENTS.md's git rules as usual: confirm the target project is a git
repository, print its current branch, and ask whether to use it or create a
new one. The files this skill writes (`.claude/hooks/session-start.sh`,
`.claude/settings.json`) are ordinary versioned project files.

## 3. Check what's already there

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
- `core.hooksPath` (`git config --get core.hooksPath`) — note whether it
  already points at this config repo's `.githooks` (see step 6). If unset or
  pointing elsewhere, it needs installing/updating.

## 4. Install the hook script

Copy [assets/session-start.sh](assets/session-start.sh) to
`.claude/hooks/session-start.sh` in the target project, verbatim — it is
already generic (it only hardcodes the agents repo's public clone URL, which
is the same for every project). Make it executable (`chmod +x`).

Do not paraphrase or hand-retype the script. Copy the file as-is, so future
re-runs of this skill can diff byte-for-byte and detect drift reliably.

## 5. Wire `.claude/settings.json`

Ensure the target's `.claude/settings.json` contains a `SessionStart` hook
entry invoking the script, and sets `worktree.baseRef` to `"head"` (see
AGENTS.md's Worktree Isolation rule — without it, worktree-isolated subagents
branch from the default branch instead of the session's actual work):

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
  },
  "worktree": {
    "baseRef": "head"
  }
}
```

- If `.claude/settings.json` doesn't exist, create it with just this content.
- If it exists, merge both keys in without disturbing any other hooks or
  settings already there. If the `SessionStart` entry with this exact command
  already exists, leave it alone; same for an existing `worktree.baseRef`.

## 6. Activate the deterministic pre-push checks (local)

The deterministic git-workflow checks (`scripts/git_workflow_rules.py` +
`.githooks/pre-push`) live in **this** config repo, not in the target project.
Activate them locally without copying any files by pointing the target repo's
`core.hooksPath` at this config repo's local clone. The hook locates its checker
script relative to itself, so it works from any repo that points at that
`.githooks`.

```bash
# Resolve this config repo's local clone root (independent of the ~/.claude
# symlink layout), then point the target repo's hooks at its .githooks.
clone_root=$(git -C "$(dirname "$(realpath ~/.claude/skills/workflow-evals)")" \
  rev-parse --show-toplevel)
git -C <target-repo> config core.hooksPath "${clone_root}/.githooks"
```

- If `core.hooksPath` is already set to that value, leave it.
- If it's set to something else (a project's own custom hooks), don't overwrite
  it silently — show the user and ask.
- In **cloud** sessions the installed SessionStart hook does the equivalent
  automatically, pointing at `~/.claude/artkoenig-agents/.githooks`, so this
  local step is only needed for local work.

Unlike the SessionStart hook (which only affects cloud sessions),
`core.hooksPath` is a local git-config setting that takes effect for **local**
pushes immediately.

## 7. Report

Tell the user:

- What was installed or updated, and what was left untouched.
- That the SessionStart hook only changes **cloud/remote** sessions
  (`CLAUDE_CODE_REMOTE=true`), while `core.hooksPath` (step 6) governs **local**
  pushes — the two cover the two environments.
- That the target environment needs GitHub access to
  `global-agents-config-and-skills` to clone it (it's a private repo), the same
  access it uses to clone the project itself.
- That the new/changed files (`.claude/hooks/session-start.sh`,
  `.claude/settings.json`) still need to be committed — per AGENTS.md's git
  rules, don't commit them yourself unless asked. (`core.hooksPath` lives in
  `.git/config`, which is not committed.)
