# global-agents-config-and-skills

Artjom König's global Claude Code configuration, personal skills and subagents.
This repository serves three roles:

1. **Global agent instructions** — `AGENTS.md` (symlinked as `~/.claude/CLAUDE.md`).
2. **Personal skills** — `skills/` (symlinked as `~/.claude/skills/`), so they
   load as personal-level skills on this machine.
3. **Personal subagents** — `agents/` (symlinked as `~/.claude/agents/`), so they
   load as user-level subagents on this machine.

There is no plugin marketplace. Environments without this machine's
`~/.claude/` — most importantly **cloud sessions** — get the same skills and
subagents through a per-project `SessionStart` hook that clones this repo
directly; see [Using this in a cloud session](#using-this-in-a-cloud-session)
below.

## The subagents

`agents/` holds six subagents whose job is to keep the main conversation's
context small: the expensive, read-heavy work happens in their context and only a
summary comes back.

| Subagent | Model | Role |
| --- | --- | --- |
| `spec-researcher` | `sonnet` | Read-only codebase/domain research that grounds a `grill-me-for-spec` session. Returns a briefing, not file dumps. |
| `issue-implementer` | `opus` | Implements **one** tracked issue in its own git worktree and commits it on its own branch. Spawn several in parallel. |
| `standards-reviewer` | `opus` | Axis A of `testing`: static-analysis gate + code-smell review of the whole codebase. |
| `spec-reviewer` | `sonnet` | Axis B of `testing`: the diff against its acceptance criteria. |
| `test-runner` | `haiku` | Axis C of `testing`: run the suite, report green/red. |
| `docs-reviewer` | `sonnet` | Axis D of `testing`: the diff against the repository's own documentation. |

Each declares the skills it needs via the `skills:` frontmatter field, so the
principles are preloaded into the subagent's context rather than costing the main
conversation anything.

### What deliberately stays in the main conversation

Subagents have no `AskUserQuestion`, so anything that must ask the user cannot be
delegated — it would invent the answers instead. That means the grilling in
`grill-me-for-spec`, the breakdown review in the decompose workflow, the branch
question in AGENTS.md's git rules, and all triage decisions stay in the main
conversation by design, not by omission.

### Running implementers in parallel

`tracker.py next --all` prints the actionable frontier — every unblocked
`ready-for-agent` leaf, hence a set that is independent by construction. The main
conversation dispatches one `issue-implementer` per id, each in its own worktree,
and merges the branches afterwards. The dispatcher must not claim the issues
itself: a worktree branches from the integration branch and would never see an
uncommitted claim. See `skills/issue-tracker/workflows/implement.md`.

## Using this in a cloud session

The local symlinks into `~/.claude/skills/` and `~/.claude/agents/` don't exist
in a fresh environment, so a **cloud session needs a project-local
`SessionStart` hook** that clones this repo and symlinks its `skills/` and
`agents/` into `~/.claude` itself. `personal_finance_v2` and `army_builder`
already have this wired into `.claude/hooks/session-start.sh`.

To set it up in another project, run the **`cloud-session-bootstrap`** skill
from within that project. It installs the hook script, wires
`.claude/settings.json` to invoke it on `SessionStart`, and is safe to re-run
to pick up updates (e.g. it added `agents/` symlinking after the subagents
above were introduced — a project whose hook predates that only loads
skills). It does not touch every project reflexively; run it deliberately, in
the project that should get this.

Because the repo is private, the environment must be authenticated to GitHub
with access to it (the same access it uses to clone the project itself). The
hook only acts when `CLAUDE_CODE_REMOTE=true`, so it's a no-op locally.

### Note: instructions and skill descriptions still travel

Unlike a plugin, this hook also copies `AGENTS.md` to `~/.claude/CLAUDE.md`
(step 4 of the script), so the global rules — "start a new project with
`grill-me-for-spec`", the subagent delegation policy, and so on — apply in
cloud sessions too, not just the skills and subagents themselves.
