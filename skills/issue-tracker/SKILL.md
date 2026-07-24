---
name: issue-tracker
description: Local, file-based issue tracker for a project, organised in two levels. A top-level main-issue — a directory under docs/issues/ with an issue.md holding the spec — maps 1:1 to one branch issue/<slug>, one worktree and one pull request; its nested child-issues are the vertical slices of that one PR. Use this skill to initialize the tracker in a project (init), to create/list/show issues, to move an issue through its lifecycle (needs-triage → needs-info → ready-for-agent → claimed → resolved, or superseded for an issue that will never be implemented), to find and implement the next child-issue ready for work (claim → implement → resolve), to break a specification down into child-issues, to close an issue as superseded/obsolete/duplicate, or to mark work resolved. Trigger it whenever the user talks about issues, tickets, tracking work, triage, backlog, "what should I work on next", "implement the next issue", working through tickets, breaking a spec/PRD into tasks, or setting up issue tracking for a repo — even if they don't name the tracker explicitly.
user-invocable: true
---

# Issue Tracker

A project's work is tracked as local markdown issues in **two levels**. A
top-level **main-issue** — a directory `NN-<slug>/` with an `issue.md` — maps
1:1 to one branch `issue/<slug>`, one worktree and one pull request, and its
`issue.md` holds the specification (PRD). The directories nested inside it are
its **child-issues**: the vertically-sliced, independently implementable units
of that one PR. Every issue is the same thing on disk, so the engine treats them
uniformly, but the shape the workflows assume is main-issue → child-issues.

A main-issue carries a `Type:` (`feature|fix|refactor|chore`) — the change
category that used to be a branch-name prefix, now that `issue/<slug>` is the
only branch pattern. Child-issues inherit it.

All file operations go through the deterministic script `scripts/tracker.py`, so
you never hand-parse or hand-edit issue markdown. Editing by hand risks breaking
the enforced state machine and the blocker rules.

## Locate the script

The skill may be installed globally or locally, so resolve its path before use:

```bash
python3 <path-to-issue-tracker-skill>/scripts/tracker.py <command> [args]
```

By default the tracker lives at `docs/issues/`. Set the env var
`ISSUE_TRACKER_DIR` only if a project deliberately uses another location.

## Layout

```
docs/issues/
  01-checkout-redesign/      # a main-issue → branch issue/checkout-redesign
    issue.md                 # Type: feature; holds the specification (PRD)
    01-cart-schema/
      issue.md               # a child-issue (vertical slice)
    02-cart-api/
      issue.md               # a child-issue, Blocked by: [01]
  02-login-bug/
    issue.md                 # a second main-issue, Type: fix, needs-triage
```

An issue is addressed by its path relative to `docs/issues/`, e.g.
`01-checkout-redesign/02-cart-api`. The main-issue is implicit in the folder
nesting; `Blocked by:` references **sibling** child-issues by their numeric
prefix.

See [reference/issue-format.md](reference/issue-format.md) for the `issue.md`
structure and [reference/states.md](reference/states.md) for the state machine.

## Commands

| Command | Purpose |
| --- | --- |
| `init [--agents-file FILE]` | Create `docs/issues/`, write `docs/agents/issue-tracker.md` — renewing it, and saying so, whenever an existing copy has drifted from the current template — ensure `.scratch/` is git-ignored, and wire an `## Agent skills → Issue tracker` note into `AGENTS.md`/`CLAUDE.md` (idempotent). |
| `create --title T --type {feature,fix,refactor,chore} [--parent ID] [--status S] [--blocked-by "N,N"]` | Create an issue. `--type` is required for a main-issue and inherited by a child-issue (`--parent`). Defaults to `needs-triage`. Prints the new issue id. |
| `list [--parent ID] [--status S] [--tree]` | List issues, optionally scoped to a subtree or filtered by status. |
| `show ID` | Print an issue's markdown. |
| `set-status ID STATE [--reason "why"]` | Move an issue to a new state. Invalid transitions and resolving a parent with open children are rejected. `--reason` is required for `superseded` and is recorded as a comment. |
| `comment ID "text"` | Append a note under `## Comments`. |
| `next [--parent ID] [--all]` | Print the next actionable **child-issue** (a leaf): `ready-for-agent`, all sibling blockers closed. Scope to one main-issue with `--parent`. With `--all`, print every such issue — the full actionable frontier. Child-issues are implemented one at a time in dependency order, so the loop normally consumes them via plain `next`; `--all` is just an overview of what is unblocked. |
| `selftest` | Run the engine's built-in tests. |

## When to use which workflow

Most operations are single commands. Two operations are reasoning-heavy and have
their own guides — read them when you reach that step:

- **Breaking a specification into issues** — when a main-issue's specification
  (PRD) must be turned into implementable, vertically-sliced child-issues, follow
  [workflows/decompose.md](workflows/decompose.md).
- **Implementing tracked issues** — to work through the open issues, follow
  [workflows/implement.md](workflows/implement.md). Child-issues are implemented
  **sequentially, one at a time** in dependency order: preferably by dispatching
  one `issue-implementer` subagent per slice (so the implementation stays out of
  the main conversation), or inline as a fallback. Implementers never run in
  parallel.
- **Resolving an implemented issue** — when an issue has been implemented and its
  tests pass, follow [workflows/resolve.md](workflows/resolve.md) to record the
  outcome and set `resolved`.

## Typical flows

**Set up tracking in a repo**
```bash
python3 <skill>/scripts/tracker.py init
```

**File a freshly reported bug** (a main-issue entering the triage inbox)
```bash
python3 <skill>/scripts/tracker.py create --title "Login crashes on empty password" --type fix
```

**Pick up and complete the next task**
```bash
ID=$(python3 <skill>/scripts/tracker.py next)
python3 <skill>/scripts/tracker.py set-status "$ID" claimed
# ...implement (see workflows/implement.md), then:
python3 <skill>/scripts/tracker.py set-status "$ID" resolved
```

**See the whole actionable frontier (everything currently unblocked)**
```bash
python3 <skill>/scripts/tracker.py next --all
```

**Close an issue that will never be implemented** (replaced, obsolete, duplicate)
```bash
python3 <skill>/scripts/tracker.py set-status "$ID" superseded \
  --reason "Subsumed by 03-cart-rewrite, which covers the same behavior."
```
`superseded` is reachable from every open state but not from `resolved`, the
reason is mandatory and recorded as a comment, and the state counts as closed —
it releases blocked siblings and does not hold up its main-issue. See
[reference/states.md](reference/states.md).

## Relationship to other skills

- **grill-me-for-spec** produces a specification (PRD) and then creates the
  **main-issue** to hold it (with its `Type:`). The decompose workflow slices
  that main-issue's spec into child-issues.
- Implementation of tracked issues is handled by this skill's
  [implement workflow](workflows/implement.md); `init` also writes that workflow
  into the project's `docs/agents/issue-tracker.md`, so an agent working an
  initialized repo knows the loop without invoking a skill.
