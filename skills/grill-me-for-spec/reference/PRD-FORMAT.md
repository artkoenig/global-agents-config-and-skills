# PRD Format

A PRD (Product Requirements Document) is the specification produced by the
grilling session. It captures the shared understanding reached with the user —
the problem, the chosen solution, the requirements, and the key technical and
testing decisions — without drifting into an implementation plan.

The PRD is the **output** of `grill-me-for-spec` and the **input** to any
downstream decomposition or planning step that slices the specification into
implementable work.

## Structure

ALWAYS use this template:

```markdown
# PRD: [Name]

## Problem Statement / Bug Description
[The problem to solve or the bug to fix. For a bug: current vs. expected behavior.]

## Solution
[The chosen approach, at a conceptual level.]

## User Stories / Requirements
1. As an [Actor], I want [Capability], in order to [Benefit].

## Technical Decisions
- Affected Modules:
- Technical Clarifications / Architectural Decisions:
- API Contracts / Data Models:

## Testing Decisions
- Modules to Test:
- Test Interfaces (Seams):

## Out of Scope
- [Things explicitly not part of this change.]
```

## Rules

- **Specify, don't plan.** Describe *what* and *why*, not a step-by-step *how*.
  No implementation plan, no code, no file-by-file task list — that is the job of
  decomposition and implementation.
- **Behavior over paths.** Prefer describing observable behavior to naming
  concrete files, which go stale quickly.
- **Link decisions out.** Record genuine architectural trade-offs as ADRs (see
  [ADR-FORMAT.md](ADR-FORMAT.md)) and domain terms in `CONTEXT.md` (see
  [CONTEXT-FORMAT.md](CONTEXT-FORMAT.md)); reference them here rather than
  duplicating.
- **Keep Out of Scope honest.** Naming what is excluded prevents scope creep and
  sets expectations for the decomposition.
