# Issue states

Every issue carries exactly one of six states in its `Status:` line. The states
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
- `superseded` — closed **without** being implemented: replaced by another
  issue, made obsolete by a merged change, a dropped requirement, or a
  duplicate. Which of those it was is stated in the mandatory reason, not in the
  state name — one state covers all of them.

`resolved` and `superseded` are the two **closed** states: an issue in either
will see no further work. Everything that asks "is this issue still open?" —
blocker satisfaction, the main-issue resolution gate — treats them alike.

## Allowed transitions

```
needs-triage    → needs-info | ready-for-agent | superseded
needs-info      → ready-for-agent | needs-triage | superseded
ready-for-agent → claimed | needs-info | superseded
claimed         → resolved | ready-for-agent | superseded   (release the claim)
resolved        → ready-for-agent                            (reopen)
superseded      → needs-triage                               (reopen)
```

Any other transition is rejected by `tracker.py set-status`. Setting an issue to
its current state is a no-op and always allowed.

`superseded` is reachable from every open state — work already in progress can
become obsolete too — but **not** from `resolved`: finished work is not undone
after the fact, that would falsify the history. The way back out of `superseded`
is `needs-triage`, symmetric to reopening a `resolved` issue.

## Superseding an issue requires a reason

The transition to `superseded` demands a justification and is rejected without
one:

```bash
python3 <skill>/scripts/tracker.py set-status <id> superseded \
  --reason "Subsumed by 03-cart-rewrite, which covers the same behavior."
```

The reason is appended to the issue's `## Comments`, where every other note on
the issue lives. Without this rule an issue could vanish from the board with no
record of why — exactly what the state machine prevents everywhere else.

## Main-issue / child-issue rule

A main-issue cannot be set to `resolved` while any child-issue is still open —
that is, in neither closed state. A `superseded` child-issue therefore does not
hold up its main-issue: a slice that will never be built must not block the PR
forever. Because closing each child-issue is itself guarded, a main-issue is
"done" — and its pull request ready to open — only once its whole subtree is
closed.

The same holds for blockers: a `superseded` blocker releases the issues it
blocks, just as a `resolved` one does.

## How states map to work

- New bug reports and ideas start at `needs-triage`.
- The decompose workflow creates child-issues directly at `ready-for-agent`,
  because they come from an already-specified main-issue, and advances the
  main-issue itself to `ready-for-agent` once it has been sliced.
- `next` returns any `ready-for-agent` **leaf** issue (a directory with no
  children of its own) whose blockers are all closed. For a normal,
  multi-slice main-issue that leaf is always a child-issue. But when a
  specification only ever yields a single slice, decompose.md folds it
  directly into the main-issue instead of creating a lone child-issue for it
  (see decompose.md, "single slice: fold into the main-issue") — that
  main-issue then has no children, so it is itself the leaf `next` returns.
  The main-issue/child-issue rule above still holds either way: with zero
  children, "no child-issue is open" is vacuously true, so the main-issue
  moves through `claimed` → `resolved` like any other leaf.
- An issue that turns out never to be worth building — subsumed by another
  issue, obsoleted by a merged pull request, or a duplicate — is closed as
  `superseded` with the reason, from whichever state it currently sits in.
