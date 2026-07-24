# Workflow: Implement tracked issues

Use this workflow to implement a **main-issue** — to work through all the
child-issues that make up its one branch `issue/<slug>`, one worktree (locally)
and one pull request. Each child-issue's lifecycle runs
`ready-for-agent → claimed → resolved`; the tracker enforces the transitions, so
all state changes go through `tracker.py`. The pull request is opened only once
every child-issue is closed and the main-issue itself is `resolved`.

Child-issues are implemented **sequentially — one after another, never in
parallel**. There is no per-child worktree and no child branch to merge: each
slice is built directly in the session's working tree on the main-issue branch
(locally inside its worktree, in cloud sessions directly in the per-session
clone), and the next slice starts only once the current one is done.

Before this workflow runs, the [architect workflow](architect.md) has usually
produced a temporary `docs/issues/<main-id>/design.md`: the module-level plan the
slices are built against. Each `issue-implementer` reads it, so the sequentially
built slices share module boundaries and contracts instead of each inventing
their own. It is a working artifact, not part of the deliverable — it is deleted
at the resolution gate (step 3) so it never lands in the PR. A single-slice
main-issue usually has none (the architect step is skipped for it).

A child-issue that turns out never to be needed — its work is already covered
elsewhere, or the requirement fell away mid-implementation — is not left hanging
and not faked as implemented. Close it as `superseded` with a mandatory reason:

```bash
python3 <skill>/scripts/tracker.py set-status "<child-id>" superseded \
  --reason "Already covered by 02-cart-api; nothing left to build here."
```

`superseded` counts as closed: it releases the siblings that were blocked on it
and does not hold up the main-issue's resolution. It is reachable from every
open state, including `claimed`. Use it only for work that will genuinely never
be done — never to make a failing slice go away.

Resolve `<skill>` below to the path of the `issue-tracker` skill's script.

There are two shapes, depending on the main-issue. Use **section A** when the
main-issue has child-issues. Use **section B** when it has **none** —
decompose.md folded a single slice directly into it, so there is nothing for
`next --parent` to find (that only ever returns descendants).

---

## A. Main-issue with child-issues (sequential)

Work the child-issues one at a time, in dependency order, on the main-issue
branch. Each slice is built in the session's own checkout; you never spawn more
than one implementer at a time.

Two ways to run each slice — both sequential:

- **Delegate (preferred).** Dispatch a single `issue-implementer` subagent for
  the current child-issue. It claims, implements, verifies and resolves that one
  slice, editing the working tree in place, and hands it back **uncommitted**.
  This keeps the implementation out of the main conversation's context — you
  hold only the slice's summary. Dispatch the next implementer only once this
  one has returned.
- **Inline (fallback).** When the `issue-implementer` subagent is unavailable,
  implement the child-issue yourself in the session, following the same steps.

### 1. Claim the main-issue

Claim the **main-issue** (once) — it stays `claimed` for as long as any of its
child-issues are being worked, not just for an instant right before the whole
subtree resolves:
```bash
python3 <skill>/scripts/tracker.py set-status "<main-id>" claimed
```
Setting an already-`claimed` main-issue to `claimed` again is a no-op, so this is
safe to repeat.

### 2. Work the next actionable child-issue

```bash
ID=$(python3 <skill>/scripts/tracker.py next --parent <main-id>)
```
`next` returns the next unblocked `ready-for-agent` child-issue (numeric
dependency order). If nothing is returned, there is no ready work — go to
step 3.

**Delegating:** dispatch one `issue-implementer` with:

- **issue_id** — the id from `next`.
- **tracker_script** — the resolved path to `scripts/tracker.py`.
- **design_path** (if the architect step ran) — the path to the main-issue's
  `design.md`, so the implementer builds its slice against the shared module
  boundaries and contracts.

The implementer claims the child itself, implements only that slice, runs the
test suite via `test-runner`, and resolves it. Do not restate its rules; its
definition carries them. When it returns, review its acceptance-criteria table
and its note about what it touched.

**Inline:** claim and read it, then implement it yourself:
```bash
python3 <skill>/scripts/tracker.py set-status "$ID" claimed
python3 <skill>/scripts/tracker.py show "$ID"
```
Implement **only** what this child-issue specifies — do not anticipate other
child-issues. Follow the `engineering-principles` skill (meaningful names,
single responsibility, comprehensive tests). Run the project's test suite and
verify it passes and the acceptance criteria are met, then resolve it via
[resolve.md](resolve.md).

Either way, the slice's work now sits **uncommitted** in the session's working
tree together with its tracker status change. Per AGENTS.md's git rules you do
not commit it on your own initiative while siblings are still open — the work
accumulates on the branch and is committed at the resolution gate (step 3). If I
explicitly ask for an intermediate commit, that is fine; otherwise leave it.

### 3. Continue or finish

Repeat step 2 until `next --parent <main-id>` returns nothing. Then check
whether the whole subtree is closed:

```bash
python3 <skill>/scripts/tracker.py list --parent "<main-id>"
```

If every child-issue is now closed (`resolved`, or `superseded` for a slice that
turned out not to be needed), follow [resolve.md](resolve.md) on the
**main-issue id** — it was already claimed in step 1, so this runs the full
five-axis `review` skill, resolves the main-issue, then automatically commits,
pushes and opens the PR (resolve.md steps 4–5). resolve.md deletes the temporary
`design.md` before that commit, so the plan never lands in the PR. That is where
the accumulated child work is committed. One PR for the whole main-issue. If
child-issues remain open (blocked, or awaiting info), leave the main-issue alone;
it isn't done yet.

### 4. Report

Summarize per child-issue: id and final status. Include whether the main-issue
resolved and the PR is ready.

---

## B. Single-slice main-issue (no child-issues)

Use this when [decompose.md](decompose.md) folded a single slice directly into
the main-issue instead of creating a lone child-issue for it. The main-issue's
own `## Acceptance Criteria` already holds that slice's plan, and the
main-issue is already `ready-for-agent`. There is no child-issue layer here at
all — work the main-issue id directly.

### 1. Find and claim it

Because it has no children, `next --parent <main-id>` would search only its
(nonexistent) descendants and find nothing — do not use it. Either you already
know the id from decompose.md's handoff, or an unscoped `next` (no `--parent`)
will surface it once it is `ready-for-agent`, since a childless issue is a leaf
like any other:

```bash
python3 <skill>/scripts/tracker.py set-status "<main-id>" claimed
python3 <skill>/scripts/tracker.py show "<main-id>"
```

### 2. Implement

Implement the main-issue's `## Acceptance Criteria` on its own branch
`issue/<slug>`, in the session's checkout (locally its worktree, in cloud
sessions the clone). Follow the `engineering-principles` skill. Then run the
project's test suite and verify it passes.

Do not dispatch this to `issue-implementer`: that subagent's Verify step runs
only the test suite, on the premise that the full five-axis check happens once
at the main-issue level afterward (see resolve.md). A single-slice main-issue
*is* that main-issue level — its resolution gate still needs the full
`review` skill, so implementing it as if it were an ordinary child-issue would
skip that gate.

### 3. Resolve

Follow [resolve.md](resolve.md) on the main-issue id. Because the id has no
`/`, resolve.md correctly identifies it as a main-issue (not by checking for
children, which it has none of) and runs the full five-axis `review` skill
before resolving, committing, pushing, and opening the PR — exactly as it would
for a multi-slice main-issue once its whole subtree finishes.

---

## Note

This workflow is also written into a project by `tracker.py init` (into
`docs/agents/issue-tracker.md`), so an agent working in an initialized project
knows how to implement tracked work without invoking this skill explicitly.
