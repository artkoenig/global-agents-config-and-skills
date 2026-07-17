# `issue.md` format

Each issue is a directory `NN-<slug>/` containing a single `issue.md`. A
top-level directory is a **main-issue**; the directories nested inside it are its
**child-issues**. The file has a small line-based header followed by markdown
sections, so the tracker can read and update fields deterministically.

## Structure

```markdown
Status: needs-triage
Type: feature
Blocked by: None

## Description
What this issue is about / what to build. For a main-issue this section holds the
specification (PRD).

## Acceptance Criteria
- [ ] Observable, verifiable criterion
- [ ] ...

## Comments
- Notes and feedback appended during implementation.
```

## Header fields

- **`Status:`** — one of the five states (see [states.md](states.md)). Managed
  via `tracker.py set-status`.
- **`Type:`** — the change category, one of `feature | fix | refactor | chore`.
  Required on a main-issue: it replaces the old branch-name prefix now that
  `issue/<slug>` is the only branch pattern, and maps 1:1 to that branch. A
  child-issue inherits its main-issue's type unless `create --type` overrides it.
  Set at creation via `tracker.py create --type`.
- **`Blocked by:`** — either `None` or a list of **sibling** numeric prefixes,
  e.g. `[01, 03]`. A blocker is satisfied when that sibling reaches `resolved`.
  Blockers only reference child-issues under the same main-issue.

## Addressing

An issue's id is its path relative to `docs/issues/`, e.g.
`01-checkout-redesign/02-cart-api`. The main-issue is implicit in the folder
nesting, so there is no explicit parent field.

## Conventions

- Numeric prefixes (`01`, `02`, …) are unique within a main-issue and define
  order. Because a child-issue can only block a sibling that already exists, its
  blockers always carry a lower prefix — so numeric order is a valid dependency
  order, and thus a valid merge order.
- Keep the `## Description` free of concrete file paths where possible — they go
  stale quickly. Describe end-to-end behavior instead.
- Do not hand-edit the header. Use the tracker so state and blocker rules hold.
