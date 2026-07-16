# Workflow: Implement tracked issues

Use this workflow to work through the open issues of a project. Each issue's
lifecycle runs `ready-for-agent → claimed → resolved`; the tracker enforces the
transitions, so all state changes go through `tracker.py`.

Resolve `<skill>` below to the path of the `issue-tracker` skill's script.

There are two ways to run this. **Prefer parallel dispatch** — it keeps the
implementation out of the main conversation's context entirely. Fall back to the
sequential loop when the `issue-implementer` subagent is unavailable, or when a
single issue is all that is left.

---

## A. Parallel dispatch (preferred)

Spawn one `issue-implementer` subagent per issue, each in its own git worktree,
then merge their branches. You stay the dispatcher: you never read the code, and
your context holds only the issues' summaries.

### 1. Read the actionable frontier

```bash
python3 <skill>/scripts/tracker.py next --all
```

`next --all` prints every unblocked `ready-for-agent` **leaf** issue, one per
line. Because a blocked issue is excluded by definition, everything printed is
independent of everything else printed — this list *is* the parallel-safe set.
Add `--parent <id>` to focus on one feature.

If nothing is printed, there is no ready work. Stop and report.

### 2. Do not claim the child issues yourself

Leave their statuses alone. Each implementer claims its own issue inside its own
worktree, and that claim comes back to you with its merge. A claim you make here
would sit uncommitted in your checkout, never reach the worktrees (they branch
from the integration branch, not your `HEAD`), and then conflict on merge. The
parent feature is different — you claim that yourself, in step 3.

### 3. Dispatch

Before spawning, claim each dispatched issue's **parent feature** (if it has
one), the same moment you would claim the issue itself if it had no subagent to
do that for it. A feature is `claimed` for as long as any of its children are
being worked — not just for an instant right before the whole subtree resolves:
```bash
for ID in <ids you are about to dispatch>; do
  PARENT=$(dirname "$ID")
  [ "$PARENT" != "." ] && python3 <skill>/scripts/tracker.py set-status "$PARENT" claimed
done
```
Setting an already-`claimed` parent to `claimed` again is a no-op, so this is
safe to repeat across dispatch rounds.

Agree with the user how many to run at once, then spawn that many
`issue-implementer` subagents **in a single message** so they run concurrently.
Give each one exactly one issue:

- **issue_id** — one id from step 1. Never the same id to two agents.
- **tracker_script** — the resolved path to `scripts/tracker.py`.
- **branch_name** (optional) — defaults to `issue/<slug>`.

Do not restate the implementation rules; the subagent's definition carries them.

Parallelism is only as safe as the tracker's blocker graph is honest. If two
frontier issues obviously touch the same code and no `Blocked by:` says so, the
graph is wrong. Fix the blockers, or run those two sequentially, and tell the
user why.

### 4. Merge

Each implementer returns a branch, a commit, and a note about what it touched.
Merge them into the integration branch one at a time, running the test suite
after each merge — a set of individually green branches is not a green merge.

Merging happens in the **user's** checkout, so AGENTS.md's git rules apply in full:
the worktree commit exception does not reach here. Ask before committing a merge,
and never push on your own.

On a conflict, resolve it or hand it to the user. Do not send it back to an
implementer: its worktree is branched from the integration branch and knows
nothing of its siblings.

### 5. Resolve completed features

`next`/`next --all` only ever return leaf issues, so nothing surfaces a finished
**feature** automatically — check it yourself. For each parent touched by this
batch:

```bash
python3 <skill>/scripts/tracker.py list --parent "<parent-id>"
```

If every child now shows `resolved`, follow [resolve.md](resolve.md) on the
**parent id** — it was already claimed in step 3, so this runs `testing`,
resolves it, and reports. If children remain open (elsewhere in the frontier, or
blocked), leave the parent alone; it isn't done yet.

### 6. Report

Summarize per issue: id, final status, branch, and whether it merged cleanly.
Include the outcome of any feature resolved in step 5.

---

## B. Sequential loop (fallback)

Work the issues one at a time, in the user's checkout.

### 1. Find the next actionable issue
```bash
ID=$(python3 <skill>/scripts/tracker.py next)
```
`next` returns the next unblocked `ready-for-agent` **leaf** issue. Add
`--parent <id>` to focus on a single feature. If nothing is returned, there is no
ready work — stop and report.

Claim it and read it:
```bash
python3 <skill>/scripts/tracker.py set-status "$ID" claimed
python3 <skill>/scripts/tracker.py show "$ID"
```

If `$ID` has a parent (a feature), claim the parent too, unless it already is —
a feature is `claimed` for as long as any of its children are being worked, not
just for an instant right before the whole subtree resolves:
```bash
PARENT=$(dirname "$ID")
[ "$PARENT" != "." ] && python3 <skill>/scripts/tracker.py set-status "$PARENT" claimed
```

### 2. Implement
Implement **only** what this issue specifies — do not anticipate other issues.
Work in small increments on a branch (e.g. `issue/<slug>`). For the coding
itself, follow the `engineering-principles` skill (meaningful names, single
responsibility, comprehensive tests). Then run the project's test suite and
verify all tests pass and the issue's acceptance criteria are met.

### 3. Resolve
Follow [resolve.md](resolve.md): append a short solution summary as a comment and
set the status to `resolved`.

### 4. Continue or hand off
Repeat from step 1. When no ready issues remain, check whether the parent feature
you were working under is now fully resolved:
```bash
python3 <skill>/scripts/tracker.py list --parent "<parent-id>"
```
If every child shows `resolved`, follow [resolve.md](resolve.md) on the parent id
— it was already claimed in step 1, so this runs `testing`, resolves it, and
reports. Only then give the user a brief summary of the changes made and the
state of the git repository.

---

## Note

This workflow is also written into a project by `tracker.py init` (into
`docs/agents/issue-tracker.md`), so an agent working in an initialized project
knows how to implement tracked work without invoking this skill explicitly.
