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
The problem to solve and the desired observable behavior — never a technical
solution or code. For a main-issue this section holds the specification (PRD).

## Acceptance Criteria
- [ ] Observable criterion, verifiable in domain terms
- [ ] ...

## Comments
- Notes and feedback appended during implementation.
```

## Header fields

- **`Status:`** — one of the six states (see [states.md](states.md)). Managed
  via `tracker.py set-status`. Moving an issue to `superseded` — closed without
  ever being implemented — additionally requires `--reason`, which is recorded
  under `## Comments`.
- **`Type:`** — the change category, one of `feature | fix | refactor | chore`.
  Required on a main-issue: it replaces the old branch-name prefix now that
  `issue/<slug>` is the only branch pattern, and maps 1:1 to that branch. A
  child-issue inherits its main-issue's type unless `create --type` overrides it.
  Set at creation via `tracker.py create --type`.
- **`Blocked by:`** — either `None` or a list of **sibling** numeric prefixes,
  e.g. `[01, 03]`. A blocker is satisfied when that sibling is closed — either
  `resolved` or `superseded`, since a sibling that will never be built must not
  block forever. Blockers only reference child-issues under the same main-issue.

## Addressing

An issue's id is its path relative to `docs/issues/`, e.g.
`01-checkout-redesign/02-cart-api`. The main-issue is implicit in the folder
nesting, so there is no explicit parent field.

## Conventions

- Numeric prefixes (`01`, `02`, …) are unique within a main-issue and define
  order. Because a child-issue can only block a sibling that already exists, its
  blockers always carry a lower prefix — so numeric order is a valid dependency
  order, and thus a valid merge order.
- **Describe the problem, not the solution.** Keep the `## Description` free of a
  prescribed technical approach, code fragments, and concrete file paths — they
  pre-empt a possibly better implementation and go stale quickly. State the
  end-to-end behavior the change must produce; leave *how* to implementation.
- **Acceptance criteria are domain-level.** Each criterion must be observable and
  verifiable using only domain knowledge (the glossary in `CONTEXT.md`), without
  any knowledge of the concrete implementation. A criterion that names internal
  functions, modules, or code structure is written at the wrong level — restate
  it as the behavior a domain expert would check.
- **Genuine settled decisions** — hard-to-reverse architectural trade-offs — are
  recorded as ADRs under `docs/adr/` and referenced, not spelled out as
  implementation in the issue body.
- Do not hand-edit the header. Use the tracker so state and blocker rules hold.
