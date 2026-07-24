# PRD Format

A PRD (Product Requirements Document) is the specification produced by the
grilling session. It captures the shared understanding reached with the user —
the problem, the desired observable behavior, the requirements, and any genuinely
settled decisions — **without prescribing how to build it**. It deliberately
leaves the technical solution open, so the implementer can still find a better
alternative or rightly challenge the existing implementation.

The PRD is the **output** of `grill-me-for-spec` and the **input** to any
downstream decomposition or planning step that slices the specification into
implementable work.

## Structure

ALWAYS use this template:

```markdown
# PRD: [Name]

## Problem Statement / Bug Description
[The problem to solve or the bug to fix, in domain terms. For a bug: current vs.
expected behavior — what is observed vs. what a domain expert would expect.]

## Desired Behavior / Outcome
[The observable outcome that resolves the problem, described as behavior, not as
an implementation. What must be true for a domain expert to consider this done —
never how the code should achieve it.]

## User Stories / Requirements
1. As an [Actor], I want [Capability], in order to [Benefit].

## Constraints & Settled Decisions
- [Only genuine, already-agreed constraints and hard-to-reverse architectural
  decisions belong here, each with its rationale. Record such a decision as an
  ADR under docs/adr/ and reference it — do not restate it as pseudo-code or a
  data model. Everything the implementation is still free to choose stays OUT.]
- Relevant ADRs: [links, or "None"]

## Testing Decisions
- Behavior to verify: [the observable behaviors the change must be tested
  against, in domain terms.]
- Test Interfaces (Seams): [the public, observable interfaces where that behavior
  is checked — existing ones preferred; named by what they expose to a caller,
  not by internal structure.]

## Out of Scope
- [Things explicitly not part of this change.]
```

## Rules

- **Specify the problem and the behavior, not the solution.** Describe *what*
  must be true and *why*, never *how* to build it. No implementation plan, no
  code, no code fragments, no file-by-file task list, and no prescribed API
  contracts, schemas, or data models — those decisions belong to implementation,
  where a better alternative may surface. Freezing them in the spec throws that
  choice away.
- **Domain terms only.** Everything a reader must verify — behavior,
  requirements, the eventual acceptance criteria — is expressed in the project's
  glossary (`CONTEXT.md`), so it can be understood and checked without any
  knowledge of the concrete implementation. If a criterion can only be judged by
  someone who has read the code, it is written at the wrong level.
- **Genuine decisions become ADRs.** A real, deliberately settled architectural
  trade-off is recorded as an ADR (see [ADR-FORMAT.md](ADR-FORMAT.md)) and
  referenced here with its rationale — not duplicated as pseudo-implementation.
  If a decision is not worth an ADR, it is not settled: leave it open for
  implementation.
- **Behavior over paths.** Prefer describing observable behavior to naming
  concrete files or modules, which go stale quickly and leak implementation.
- **Keep Out of Scope honest.** Naming what is excluded prevents scope creep and
  sets expectations for the decomposition.
