# Issue states

Every issue carries exactly one of five states in its `Status:` line. The states
form a small, enforced state machine so that a work item's lifecycle stays
meaningful — an issue cannot silently jump from "just reported" to "done".

## The states

- `needs-triage` — awaiting evaluation by the maintainer. The default for a
  newly filed issue (e.g. a reported bug or a raw idea) that has not yet been
  assessed.
- `needs-info` — blocked on a question; waiting for feedback before it can be
  specified further.
- `ready-for-agent` — fully specified and unambiguous, ready for autonomous
  implementation (AFK / "away from keyboard").
- `claimed` — currently being implemented by an agent.
- `resolved` — implemented and done, tests passing.

## Allowed transitions

```
needs-triage    → needs-info | ready-for-agent
needs-info      → ready-for-agent | needs-triage
ready-for-agent → claimed | needs-info
claimed         → resolved | ready-for-agent   (release the claim)
resolved        → ready-for-agent               (reopen)
```

Any other transition is rejected by `tracker.py set-status`. Setting an issue to
its current state is a no-op and always allowed.

## Main-issue / child-issue rule

A main-issue cannot be set to `resolved` while any child-issue is still open.
Because resolving each child-issue is itself guarded, a main-issue is "done" —
and its pull request ready to open — only once its whole subtree is `resolved`.

## How states map to work

- New bug reports and ideas start at `needs-triage`.
- The decompose workflow creates child-issues directly at `ready-for-agent`,
  because they come from an already-specified main-issue, and advances the
  main-issue itself to `ready-for-agent` once it has been sliced.
- `next` returns any `ready-for-agent` **leaf** issue (a directory with no
  children of its own) whose blockers are all `resolved`. For a normal,
  multi-slice main-issue that leaf is always a child-issue. But when a
  specification only ever yields a single slice, decompose.md folds it
  directly into the main-issue instead of creating a lone child-issue for it
  (see decompose.md, "single slice: fold into the main-issue") — that
  main-issue then has no children, so it is itself the leaf `next` returns.
  The main-issue/child-issue rule above still holds either way: with zero
  children, "no child-issue is open" is vacuously true, so the main-issue
  moves through `claimed` → `resolved` like any other leaf.
