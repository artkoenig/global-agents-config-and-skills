---
name: grill-me-for-spec
description: Interactive requirements-analysis and domain-modeling session that turns a vague idea, feature request, or bug into a written specification (a PRD file). It relentlessly grills the user one question at a time, researches the codebase, refines the domain glossary (CONTEXT.md) and architectural decision records (ADRs) as it goes, and writes a completed PRD as its output. Use this whenever the user wants to specify a new feature or change, flesh out requirements, "think through" or "spec out" something before building, analyze a bug's real cause, or produce a PRD — for either a whole project or a single feature or change. Trigger it on phrases like "help me spec this", "grill me", "let's nail down the requirements", "write a PRD for", or when a request is too underspecified to implement safely. Do not use it to break a finished spec into tasks or to write code.
user-invocable: true
---

# Grill Me For Spec

Turn a rough idea, feature request, or bug into a precise, written specification
(a PRD). The goal is a **shared, unambiguous understanding** captured on disk —
not an implementation plan and not code. The PRD is the sole output: a
self-contained file that a downstream decomposition or planning step can later
turn into implementable work.

This skill deliberately "grills": it asks hard questions and challenges vague or
overloaded language, because most implementation risk comes from
under-specification, not from typing speed.

## 1. Frame the request

Establish the essentials before grilling:

- Is this a **feature** or a **bug**? For a bug, capture current vs. expected
  behavior.
- What is the target of the spec — a whole **project** or a single **feature or
  change**? This frames how broadly to grill and where the PRD lands (see step 6).
- Get a one-paragraph description in the user's own words.

## 2. Context & codebase analysis

Ground the discussion in reality before asking the user anything you could find
out yourself:

- Read the domain docs (`CONTEXT.md` / `CONTEXT-MAP.md`) and respect existing
  ADRs under `docs/adr/`.
- Identify affected classes, interfaces, APIs, data models, and UI components.
- Research facts directly from the codebase instead of asking about them.

## 3. Grilling session & active domain modeling

This is the core. Relentlessly question the user on requirements and design until
a shared model emerges.

- Ask questions **one at a time**, and always offer your **recommended answer**
  with each question. Wait for the user's response before moving on.
- Walk the design tree branch by branch, resolving dependencies between decisions
  in order.
- Perform **active domain modeling** as you go:
  - Use and refine the glossary in `CONTEXT.md` / `CONTEXT-MAP.md`.
  - If the user's wording conflicts with the existing glossary, point it out
    immediately. Question vague or overloaded terms and propose precise ones.
  - Test concrete scenarios against the code to surface contradictions.
  - Once a term is clarified, update `CONTEXT.md` inline using
    [reference/CONTEXT-FORMAT.md](reference/CONTEXT-FORMAT.md). Keep it free of
    implementation detail.
  - Propose ADRs under `docs/adr/` (format:
    [reference/ADR-FORMAT.md](reference/ADR-FORMAT.md)) **sparingly**, only when
    all three hold: the decision is hard to reverse, it would surprise a future
    reader without context, and it results from a genuine trade-off.

Proceed only once the user confirms a shared understanding of model and design.

## 4. Define test interfaces (seams)

Decide at which public interfaces (seams) the change will be tested. Prefer
existing interfaces; keep new ones to a minimum. Present the proposed seams in
chat for approval — do not defer this to implementation.

## 5. Write the PRD

Synthesize everything from the discussion and codebase analysis into a completed
PRD, following [reference/PRD-FORMAT.md](reference/PRD-FORMAT.md). Do **not** run
another interview for this — use the understanding already gained in step 3.

## 6. Write the output & stop

Write the completed PRD to a single self-contained file:

- **Default:** `PRD.md` in the project root.
- **Custom location:** if the user or the invoking workflow named a target path,
  write the PRD there instead. This is how a spec for a single feature within a
  larger project is placed where its owner expects it.

Then stop. Do not generate an implementation plan and do not write code. Tell the
user the specification is complete, state where the PRD was written, and that it
is ready to be broken down into tasks or handed to a planning step.
