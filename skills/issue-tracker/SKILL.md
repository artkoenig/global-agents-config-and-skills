---
name: issue-tracker
description: Local, file-based issue tracker for a project. Everything is an issue — a directory under docs/issues/ with an issue.md — and issues nest to form features (an issue with child issues is a feature; its issue.md is the spec). Use this skill to initialize the tracker in a project (init), to create/list/show issues, to move an issue through its lifecycle (needs-triage → needs-info → ready-for-agent → claimed → resolved), to find the next issue ready for implementation, to break a specification down into child issues, or to mark work resolved. Trigger it whenever the user talks about issues, tickets, tracking work, triage, backlog, "what should I work on next", breaking a spec/PRD into tasks, or setting up issue tracking for a repo — even if they don't name the tracker explicitly.
user-invocable: true
---

# Issue Tracker

A project's work is tracked as a **recursive tree of markdown issues**. There is
only one concept — an *issue* — and issues nest arbitrarily deep, so a "feature"
is simply an issue that has child issues, and its `issue.md` is that feature's
specification. This keeps epics, features, and tasks in one uniform structure.

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
  01-checkout-redesign/      # a feature = an issue with children
    issue.md                 # the feature's specification (PRD)
    01-cart-schema/
      issue.md               # a leaf task
    02-cart-api/
      issue.md               # Blocked by: [01]
  02-login-bug/
    issue.md                 # a reported bug, Status: needs-triage, no children
```

An issue is addressed by its path relative to `docs/issues/`, e.g.
`01-checkout-redesign/02-cart-api`. Parenthood is implicit in the folder nesting;
`Blocked by:` references **sibling** issues by their numeric prefix.

See [reference/issue-format.md](reference/issue-format.md) for the `issue.md`
structure and [reference/states.md](reference/states.md) for the state machine.

## Commands

| Command | Purpose |
| --- | --- |
| `init [--agents-file FILE]` | Create `docs/issues/`, write `docs/agents/issue-tracker.md`, ensure `.scratch/` is git-ignored, and wire an `## Agent skills → Issue tracker` note into `AGENTS.md`/`CLAUDE.md` (idempotent). |
| `create --title T [--parent ID] [--status S] [--blocked-by "N,N"]` | Create an issue. Defaults to `needs-triage`. Prints the new issue id. |
| `list [--parent ID] [--status S] [--tree]` | List issues, optionally scoped to a subtree or filtered by status. |
| `show ID` | Print an issue's markdown. |
| `set-status ID STATE` | Move an issue to a new state. Invalid transitions and resolving a parent with open children are rejected. |
| `comment ID "text"` | Append a note under `## Comments`. |
| `next [--parent ID]` | Print the next actionable **leaf** issue: `ready-for-agent`, all sibling blockers `resolved`. |
| `selftest` | Run the engine's built-in tests. |

## When to use which workflow

Most operations are single commands. Two operations are reasoning-heavy and have
their own guides — read them when you reach that step:

- **Breaking a specification into issues** — when a specification/PRD exists (for
  a project or for a parent issue) and must be turned into implementable,
  vertically-sliced child issues, follow
  [workflows/decompose.md](workflows/decompose.md).
- **Resolving an implemented issue** — when an issue has been implemented and its
  tests pass, follow [workflows/resolve.md](workflows/resolve.md) to record the
  outcome and set `resolved`.

## Typical flows

**Set up tracking in a repo**
```bash
python3 <skill>/scripts/tracker.py init
```

**File a freshly reported bug** (enters the triage inbox)
```bash
python3 <skill>/scripts/tracker.py create --title "Login crashes on empty password"
```

**Pick up and complete the next task**
```bash
ID=$(python3 <skill>/scripts/tracker.py next)
python3 <skill>/scripts/tracker.py set-status "$ID" claimed
# ...implement (see the implement-with-ticket skill), then:
python3 <skill>/scripts/tracker.py set-status "$ID" resolved
```

## Relationship to other skills

- **grill-me-for-spec** produces a specification (PRD). That PRD becomes a parent
  issue's `issue.md`, which the decompose workflow slices into child issues.
- **implement-with-ticket** consumes this tracker: it calls `next`, sets
  `claimed`, implements, and finishes via the resolve workflow.
