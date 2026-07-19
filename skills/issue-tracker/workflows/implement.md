# Workflow: Implement tracked issues

Use this workflow to implement a **main-issue** — to work through all the
child-issues that make up its one branch `issue/<slug>`, one worktree and one
pull request. Each child-issue's lifecycle runs
`ready-for-agent → claimed → resolved`; the tracker enforces the transitions, so
all state changes go through `tracker.py`. The pull request is opened only once
every child-issue — and then the main-issue itself — is `resolved`.

Resolve `<skill>` below to the path of the `issue-tracker` skill's script.

There are three ways to run this, depending on the main-issue's shape.
**Prefer parallel dispatch (A)** when child-issues exist — it keeps the
implementation out of the main conversation's context entirely. Fall back to
the **sequential loop (B)** when the `issue-implementer` subagent is
unavailable, or when a single child-issue is all that is left. When the
main-issue has **no child-issues at all** — decompose.md folded a single slice
directly into it — use **section C** instead: there is nothing for `next
--parent` to find, since that only ever returns descendants.

---

## A. Parallel dispatch (preferred)

Spawn one `issue-implementer` subagent per child-issue, each in its own git
worktree, then merge their branches into the main-issue branch. You stay the
dispatcher: you never read the code, and your context holds only the issues'
summaries.

### 1. Read the actionable frontier

```bash
python3 <skill>/scripts/tracker.py next --parent <main-id> --all
```

`next --all` prints every unblocked `ready-for-agent` child-issue, one per line.
Because a blocked issue is excluded by definition, everything printed is
independent of everything else printed — this list *is* the parallel-safe set.

If nothing is printed, there is no ready work. Stop and report.

### 2. Do not claim the child-issues yourself

Leave their statuses alone. Each implementer claims its own child-issue inside
its own worktree, and that claim comes back to you with its merge. A claim you
make here would sit uncommitted in your checkout, never reach the worktrees (they
branch from the main-issue branch, not your `HEAD`), and then conflict on merge.
The main-issue is different — you claim that yourself, in step 4.

### 3. Commit the issue documentation before spawning worktrees

Each `issue-implementer` runs in a worktree that branches from the main-issue
branch and therefore sees only **committed** history — never the uncommitted
state of your checkout. The child-issues just created by
[decompose.md](decompose.md) under `docs/issues/` are typically still
uncommitted at this point. If you spawn now, no implementer can read its own
`issue.md`: the file exists only in your checkout, not in its worktree.

So the current state of the main-issue branch — including the new issue
documentation under `docs/issues/` — **must be committed before any worktree is
spawned**. Without that commit, the worktrees do not work.

This commit happens in the **user's** checkout, so AGENTS.md's "never commit
automatically" rule applies in full: do not commit on your own initiative. Ask
the user to commit the issue documentation (or for confirmation to do so), and
make explicit that dispatch cannot proceed until it is committed. Only once the
`docs/issues/` state is committed do you continue to dispatch.

### 4. Dispatch

Before spawning, claim the **main-issue** (once) — it stays `claimed` for as long
as any of its child-issues are being worked, not just for an instant right before
the whole subtree resolves:
```bash
python3 <skill>/scripts/tracker.py set-status "<main-id>" claimed
```
Setting an already-`claimed` main-issue to `claimed` again is a no-op, so this is
safe to repeat across dispatch rounds.

Agree with the user how many to run at once, then spawn that many
`issue-implementer` subagents **in a single message** so they run concurrently.
Give each one exactly one child-issue:

- **issue_id** — one id from step 1. Never the same id to two agents.
- **tracker_script** — the resolved path to `scripts/tracker.py`.
- **branch_name** (optional) — the child's own throwaway worktree branch, which
  merges into the main-issue branch and is removed afterwards. It is never pushed
  and never its own PR; the main-issue's `issue/<slug>` is the only branch that
  becomes a PR.

Do not restate the implementation rules; the subagent's definition carries them.

Parallelism is only as safe as the tracker's blocker graph is honest. If two
frontier issues obviously touch the same code and no `Blocked by:` says so, the
graph is wrong. Fix the blockers, or run those two sequentially, and tell the
user why.

### 5. Merge in dependency order

Each implementer returns a branch, a commit, and a note about what it touched.
Merge them into the main-issue branch **sequentially, in dependency order** —
which here is simply **numeric prefix order**: a child-issue can only be blocked
by a sibling that already existed when it was created, so every blocker carries a
lower prefix, and ascending numeric order therefore never merges a child before
one it depends on.

After each single merge:
- run the test suite — a set of individually green branches is not a green merge;
- remove that child's worktree (`git worktree remove <path>`) and delete its
  throwaway branch. No child branch outlives its merge.

Merging happens in the **user's** checkout, so AGENTS.md's git rules apply in
full: the worktree commit exception does not reach here. Ask before committing a
merge, and never push on your own.

On a conflict, resolve it or hand it to the user. Do not send it back to an
implementer: its worktree is branched from the main-issue branch and knows
nothing of its siblings.

### 6. Resolve the main-issue and open the PR

`next`/`next --all` only ever return child-issues, so nothing surfaces the
finished **main-issue** automatically — check it yourself:

```bash
python3 <skill>/scripts/tracker.py list --parent "<main-id>"
```

If every child-issue now shows `resolved`, follow [resolve.md](resolve.md) on the
**main-issue id** — it was already claimed in step 4, so this runs `testing`,
resolves it, then automatically pushes and opens the PR (resolve.md step 5).
That PR is opened only once the main-issue is `resolved` — one PR for the whole
main-issue. If child-issues remain open
(elsewhere in the frontier, or blocked), leave the main-issue alone; it isn't
done yet.

### 7. Report

Summarize per child-issue: id, final status, branch, and whether it merged
cleanly. Include whether the main-issue resolved and the PR is ready.

---

## B. Sequential loop (fallback)

Work the child-issues one at a time, in the main-issue's own checkout (its
worktree), on the main-issue branch.

### 1. Find the next actionable child-issue
```bash
ID=$(python3 <skill>/scripts/tracker.py next --parent <main-id>)
```
`next` returns the next unblocked `ready-for-agent` child-issue. If nothing is
returned, there is no ready work — stop and report.

Claim it and read it:
```bash
python3 <skill>/scripts/tracker.py set-status "$ID" claimed
python3 <skill>/scripts/tracker.py show "$ID"
```

Claim the **main-issue** too, unless it already is — it stays `claimed` for as
long as any of its child-issues are being worked:
```bash
python3 <skill>/scripts/tracker.py set-status "<main-id>" claimed
```

### 2. Implement
Implement **only** what this child-issue specifies — do not anticipate other
child-issues. Work in small increments on the main-issue branch `issue/<slug>`.
For the coding itself, follow the `engineering-principles` skill (meaningful
names, single responsibility, comprehensive tests). Then run the project's test
suite and verify all tests pass and the acceptance criteria are met.

### 3. Resolve
Follow [resolve.md](resolve.md): append a short solution summary as a comment and
set the status to `resolved`.

### 4. Continue or finish
Repeat from step 1, in numeric order. When no ready child-issues remain, check
whether the main-issue is now fully resolved:
```bash
python3 <skill>/scripts/tracker.py list --parent "<main-id>"
```
If every child-issue shows `resolved`, follow [resolve.md](resolve.md) on the
main-issue id — it was already claimed in step 1, so this runs `testing`,
resolves it, and automatically pushes and opens the PR. Then give the user a
brief summary of the changes made and the state of the git repository.

---

## C. Single-slice main-issue (no child-issues)

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
`issue/<slug>`, in its own worktree (see AGENTS.md's Worktree Isolation rule —
this is the main-issue-level worktree, not a throwaway child one). Follow the
`engineering-principles` skill. Then run the project's test suite and verify it
passes.

Do not dispatch this to `issue-implementer`: that subagent's Verify step runs
only the test suite, on the premise that the full four-axis check happens once
at the main-issue level afterward (see resolve.md). A single-slice main-issue
*is* that main-issue level — its resolution gate still needs the full
`testing` skill, so implementing it as if it were an ordinary child-issue would
skip that gate.

### 3. Resolve

Follow [resolve.md](resolve.md) on the main-issue id. Because the id has no
`/`, resolve.md correctly identifies it as a main-issue (not by checking for
children, which it has none of) and runs the full four-axis `testing` skill
before resolving, pushing, and opening the PR — exactly as it would for a
multi-slice main-issue once its whole subtree finishes.

---

## Note

This workflow is also written into a project by `tracker.py init` (into
`docs/agents/issue-tracker.md`), so an agent working in an initialized project
knows how to implement tracked work without invoking this skill explicitly.
