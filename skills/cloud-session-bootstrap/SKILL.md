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
- `.claude/hooks/worktree_guard.py` — read it if present, same drift check as
  above against [assets/worktree_guard.py](assets/worktree_guard.py).
- `.claude/hooks/worktree-create.sh` — read it if present, same drift check as
  above against [assets/worktree-create.sh](assets/worktree-create.sh). A repo
  wired before this hook existed won't have it at all — that is the expected
  drift, and a `WorktreeCreate` entry missing from `.claude/settings.json` (see
  below) is the same gap seen from the settings side.
- `.claude/settings.json` — read it if present. Note whether it already wires a
  `SessionStart` hook, a `PreToolUse` hook, and a `WorktreeCreate` hook. A
  `WorktreeCreate` entry that is missing, or whose command differs from the one
  in step 5 (e.g. an older inline `bash -c '…git worktree add…'` blob instead of
  the `worktree-create.sh` script), is drift to fix — without it, native
  worktree paths (`EnterWorktree`, `--worktree`, `isolation: worktree`) land in
  `.claude/worktrees/` instead of `.worktrees/`, breaking the convention
  AGENTS.md promises.
- `.gitignore` — check whether it ignores `.claude/.worktree-bypass`,
  `.worktrees/`, and `.claude/worktrees/` (see step 5b). The bypass marker in
  particular must be ignored, or a routine `git add -A` during a merge can
  commit it and disable the guard permanently for every checkout.
- `.claude/settings.json` / `.claude/settings.local.json` — check for
  leftover references to the retired marketplace (`enabledPlugins` or
  `extraKnownMarketplaces` mentioning `artkoenig`). If found, point them out
  and ask whether to remove them; don't remove silently, since they may be
  intentional in a project you don't have full context on.
- `core.hooksPath` (`git config --get core.hooksPath`) — note whether it
  already points at this config repo's `.githooks` (see step 6). If unset or
  pointing elsewhere, it needs installing/updating.

## 4. Install the hook scripts

Copy these three assets into the target project, verbatim — all are already
generic — and make each executable (`chmod +x`):

- [assets/session-start.sh](assets/session-start.sh) → `.claude/hooks/session-start.sh`
- [assets/worktree_guard.py](assets/worktree_guard.py) → `.claude/hooks/worktree_guard.py`
- [assets/worktree-create.sh](assets/worktree-create.sh) → `.claude/hooks/worktree-create.sh`

Do not paraphrase or hand-retype any of them. Copy them as-is, so future
re-runs of this skill can diff byte-for-byte and detect drift reliably. In
particular, do **not** inline `worktree-create.sh`'s logic back into
`settings.json` as a `bash -c '…'` blob: that would recreate the second,
independently drifting copy this script exists to avoid — the settings entry
references the script by path (step 5).

## 5. Wire `.claude/settings.json`

Ensure the target's `.claude/settings.json` contains a `SessionStart` hook
entry invoking `session-start.sh`, a `PreToolUse` hook entry invoking
`worktree_guard.py`, a `WorktreeCreate` hook entry invoking
`worktree-create.sh`, and sets `worktree.baseRef` to `"head"` (see AGENTS.md's
Worktree Isolation rule — without it, worktree-isolated subagents branch from
the default branch instead of the session's actual work):

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
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/worktree_guard.py"
          }
        ]
      }
    ],
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/worktree-create.sh"
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
- If it exists, merge all four keys in without disturbing any other hooks or
  settings already there. If a `SessionStart`, `PreToolUse`, or `WorktreeCreate`
  entry with this exact command already exists, leave it alone; same for an
  existing `worktree.baseRef`. If a `WorktreeCreate` entry exists but carries the
  older inline `bash -c '…git worktree add…'` blob, replace its command with the
  `worktree-create.sh` path above — that inline blob is the drift step 3 flags.
- The `WorktreeCreate` hook redirects Claude Code's native worktree paths
  (`EnterWorktree`, `--worktree`, `isolation: worktree`, background sessions)
  into `.worktrees/<name>`, so they honor this repo's `.worktrees/` convention
  and its `.gitignore` entry instead of landing in the default
  `.claude/worktrees/`. `$CLAUDE_PROJECT_DIR` is exported for every hook command,
  so the same entry works from the main checkout and from any linked worktree.
- `worktree_guard.py` is what actually enforces AGENTS.md's Worktree Isolation
  rule (see that section) — it denies an `Edit`/`Write`/`NotebookEdit` call
  that would make a non-trivial change directly in the main checkout, instead
  of leaving that rule as unverified guidance. Tell the user about its escape
  hatch: touching `.claude/.worktree-bypass` in the target project's main
  checkout disables it for a session they've explicitly told to work directly
  in the checkout.

## 5b. Ignore the worktree paths and the bypass marker

Ensure the target's `.gitignore` ignores these three, adding any that are
missing (append them under a short comment; don't disturb existing entries):

```gitignore
# Sandbox worktrees for local parallel main-issue work; see AGENTS.md
# "Worktree Isolation". Never committed.
.worktrees/
# Native Claude Code worktrees, in case the WorktreeCreate hook is ever absent.
.claude/worktrees/
# Session-scoped override for the worktree_guard.py PreToolUse hook. Local-only,
# never committed: a routine `git add -A` during a merge would otherwise sweep
# it into the commit and disable the guard permanently for every checkout.
.claude/.worktree-bypass
```

The last entry is the important one: the bypass marker (`.claude/.worktree-bypass`)
turns the guard off for the whole session, and if it were ever committed it
would turn the guard off for the whole repo, silently. Ignoring it makes that
accident impossible. Confirm with `git check-ignore .claude/.worktree-bypass`
in the target — it should print the path.

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
  `.claude/hooks/worktree_guard.py`, `.claude/hooks/worktree-create.sh`,
  `.claude/settings.json`, and any `.gitignore` additions from step 5b) still
  need to be committed — per AGENTS.md's git rules, don't commit them yourself
  unless asked. (`core.hooksPath` lives in `.git/config`, which is not committed.)
- That `worktree_guard.py` runs on every `Edit`/`Write`/`NotebookEdit` call,
  local or cloud — unlike `session-start.sh` and `core.hooksPath`, it is not
  split by environment.
