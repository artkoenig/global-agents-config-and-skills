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

## Parent / child rule

A parent issue (one with child issues) cannot be set to `resolved` while any
child is still open. Because resolving each child is itself guarded, this holds
recursively: a feature is only "done" once its whole subtree is done.

## How states map to work

- New bug reports and ideas start at `needs-triage`.
- The decompose workflow creates child issues directly at `ready-for-agent`,
  because they come from an already-specified parent, and advances the parent
  itself to `ready-for-agent` once it has been sliced.
- `next` only ever returns `ready-for-agent` leaf issues whose blockers are
  `resolved`.
