# global-agents-config-and-skills

My global Claude Code configuration, personal skills and subagents.
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

## The skills

`skills/` holds eight personal skills. Most are triggered automatically by their
`description`; a few are also `/`-invocable.

| Skill | Role |
| --- | --- |
| `grill-me-for-spec` | Interactive requirements analysis that grills you one question at a time, researches the codebase, refines the domain glossary (`CONTEXT.md`) and ADRs, writes a PRD, and opens the main-issue that carries it. |
| `issue-tracker` | Local, file-based tracker under `docs/issues/`. A main-issue maps 1:1 to one branch, worktree and PR; its nested child-issues are that PR's vertical slices. Handles init, lifecycle, breakdown and implementation. |
| `engineering-principles` | The design and implementation principles that must be read before any architectural decision or code change. Preloaded into subagents via their `skills:` frontmatter. |
| `review` | The five-axis review (Standards, Specification, Tests, Docs, Clean-Room) that orchestrates the reviewer subagents below. Axis E runs an independent `clean-room-review` design of the problem and reconciles it against the change. |
| `clean-room-review` | An independent, blind design proposal from the `clean-room-reviewer` (which never sees the code), reconciled against reality. Used standalone for design gut-checks and as Axis E of `review`. |
| `cloud-session-bootstrap` | Wires a project so its cloud sessions load these skills and subagents via a `SessionStart` hook. See [Using this in a cloud session](#using-this-in-a-cloud-session). |
| `self-test` | Runs the deterministic git checks and behavioral evals that keep this repo's own rules honest. See [Self-testing the workflow](#self-testing-the-workflow). |
| `skill-creator` | Create, edit, optimize and benchmark skills. |

## The subagents

`agents/` holds seven subagents whose job is to keep the main conversation's
context small: the expensive, read-heavy work happens in their context and only a
summary comes back.

| Subagent | Model | Role |
| --- | --- | --- |
| `spec-researcher` | `sonnet` | Read-only codebase/domain research that grounds a `grill-me-for-spec` session. Returns a briefing, not file dumps. |
| `issue-implementer` | `opus` | Implements **one** tracked issue, editing the session's working tree in place on the main-issue branch and handing the slice back uncommitted. Dispatched one at a time, never in parallel. |
| `standards-reviewer` | `opus` | Axis A of `review`: static-analysis gate + code-smell review of the whole codebase. |
| `spec-reviewer` | `sonnet` | Axis B of `review`: the diff against its acceptance criteria. |
| `test-runner` | `haiku` | Axis C of `review`: run the suite, report green/red. |
| `docs-reviewer` | `sonnet` | Axis D of `review`: the diff against the repository's own documentation. |
| `clean-room-reviewer` | `opus` | Axis E of `review`: designs an independent solution from the problem and raw data alone (it never sees the code), to challenge the implementation. Driven via the `clean-room-review` skill. |

Each declares the skills it needs via the `skills:` frontmatter field, so the
principles are preloaded into the subagent's context rather than costing the main
conversation anything.

### What deliberately stays in the main conversation

Subagents have no `AskUserQuestion`, so anything that must ask the user cannot be
delegated — it would invent the answers instead. That means the grilling in
`grill-me-for-spec`, the breakdown review in the decompose workflow, the branch
question in AGENTS.md's git rules, and all triage decisions stay in the main
conversation by design, not by omission.

### Running implementers sequentially

Child-issues are implemented **one at a time, in dependency order** — never in
parallel. `tracker.py next` returns the next unblocked `ready-for-agent` leaf;
the main conversation dispatches a single `issue-implementer` for it, and only
dispatches the next once that one returns. Each implementer edits the session's
working tree in place on the main-issue branch and hands its slice back
uncommitted — there is no per-child worktree and no branch to merge. (`next
--all` still lists the whole unblocked frontier, but as an overview, not a batch
to run at once.) See `skills/issue-tracker/workflows/implement.md`.

### Closing an issue that will never be built

Besides the implementation lifecycle (`needs-triage` → `needs-info` →
`ready-for-agent` → `claimed` → `resolved`) the tracker has a sixth state,
`superseded`: an issue that another issue subsumes, that a merged PR made
obsolete, or that is a duplicate. It is reachable from every open state but not
from `resolved`, requires a `--reason` that is recorded as a comment, and counts
as **closed** — it releases blocked siblings and does not hold up its
main-issue:

```bash
python3 skills/issue-tracker/scripts/tracker.py set-status <id> superseded \
  --reason "Subsumed by 03-cart-rewrite."
```

See `skills/issue-tracker/reference/states.md`.

## Self-testing the workflow

`AGENTS.md`, the skills and the subagents all govern how Claude Code behaves, so
every rule is bound to a test — they cannot silently drift. The `self-test`
skill drives two kinds of check:

- **Deterministic checks** — instant, no-LLM unit tests under `scripts/`
  (`test_*.py`), run with `python3 -m unittest discover -s scripts -p 'test_*.py'`.
  They cover the git-workflow rules that `.githooks/pre-push` enforces on every
  push (via `scripts/git_workflow_rules.py`): branch naming, no direct push to a
  protected branch, and no agent `Co-authored-by` trailer.
- **Behavioral evals** — full agentic scenarios, defined in `evals.json` files
  next to what they test (under `evals/agents-md/`, `agents/*/evals/` and
  `skills/*/evals/`), that verify a rule actually behaves as documented. The
  `self-test` skill spawns executor subagents in isolated worktrees, grades the
  transcripts, and reports a pass/fail table.

The rationale is captured in `PRD.md`.

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
