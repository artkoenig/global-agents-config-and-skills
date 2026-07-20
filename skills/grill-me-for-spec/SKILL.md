---
name: grill-me-for-spec
description: Interactive requirements-analysis and domain-modeling session that turns a vague idea, feature request, or bug into a written specification (a PRD file). It relentlessly grills the user one question at a time, researches the codebase, refines the domain glossary (CONTEXT.md) and architectural decision records (ADRs) as it goes, writes a completed PRD, and opens the main-issue that carries it (with its Type). Use this whenever the user wants to specify a new feature or change, flesh out requirements, "think through" or "spec out" something before building, analyze a bug's real cause, or produce a PRD — for either a whole project or a single feature or change. Trigger it on phrases like "help me spec this", "grill me", "let's nail down the requirements", "write a PRD for", or when a request is too underspecified to implement safely. Do not use it to break a finished spec into tasks or to write code.
user-invocable: true
---

# Grill Me For Spec

Turn a rough idea, feature request, or bug into a precise, written specification
(a PRD). The goal is a **shared, unambiguous understanding** captured on disk —
not an implementation plan and not code. The PRD is the output, and this skill's
closing act is to open the **main-issue** that will carry it: one top-level issue
= one branch `issue/<slug>` = one worktree = one pull request, with the PRD as
its `## Description`. A downstream decomposition step then slices that main-issue
into implementable child-issues.

This skill deliberately "grills": it asks hard questions and challenges vague or
overloaded language, because most implementation risk comes from
under-specification, not from typing speed.

## 1. Frame the request

Establish the essentials before grilling:

- What **type** of change is this — `feature`, `fix`, `refactor`, or `chore`?
  This becomes the main-issue's `Type:` in step 6 (it replaces the old
  branch-name prefix). For a `fix`, capture current vs. expected behavior.
- What is the target of the spec — a whole **project** or a single **feature or
  change**? This frames how broadly to grill; either way the result is one
  main-issue holding the PRD (the PRD is always decomposed into a single
  main-issue plus child-issues).
- Get a one-paragraph description in the user's own words.

## 2. Context & codebase analysis

Ground the discussion in reality before asking the user anything you could find
out yourself:

- Read the domain docs (`CONTEXT.md` / `CONTEXT-MAP.md`) and respect existing
  ADRs under `docs/adr/`.
- Identify affected classes, interfaces, APIs, data models, and UI components.
- Research facts directly from the codebase instead of asking about them.

**Delegate this research to the `spec-researcher` subagent.** It reads the code,
the glossary and the ADRs in its own context and returns a briefing: current
behavior, existing commitments, blast radius, collisions, and the open questions
only the user can answer. That keeps dozens of files out of this conversation, so
the context you have left is spent on the grilling itself — which is the part
that actually needs you.

The grilling in step 3 stays here and must not be delegated: a subagent cannot
ask the user anything, so it would invent the answers instead of getting them.

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

## 6. Create the main-issue and store the spec

The PRD is not left standing as its own file — it becomes the `## Description` of
a new **main-issue**, the single home for the spec. Do this without asking:
tracking is mandatory for every non-trivial change.

Use the `issue-tracker` skill's `tracker.py` (resolve its path as that skill
documents). Ensure the tracker is initialized — `init` is idempotent — then
create the main-issue with the `Type:` you framed in step 1:

```bash
python3 <issue-tracker-skill>/scripts/tracker.py init
python3 <issue-tracker-skill>/scripts/tracker.py create \
  --title "<main-issue name>" --type <feature|fix|refactor|chore>
```

`create` prints the new main-issue id (e.g. `01-checkout-redesign`) and starts it
at `needs-triage` — specified, but not yet sliced. Choose the title so its slug
matches the work's branch `issue/<slug>` (decided upfront per the git rules),
keeping the 1:1 main-issue ↔ branch mapping honest.

Then write the PRD body into that main-issue's `## Description` with a plain file
edit — replace the placeholder line, and leave `## Acceptance Criteria` and
`## Comments` untouched (only the header and `## Comments` are tracker-managed;
see the `issue-tracker` skill's `reference/issue-format.md`). Do not also leave a
standalone `PRD.md` behind: the `## Description` is the one copy of the spec, so
it cannot drift.

If the new spec makes an **existing** issue redundant — the new main-issue
subsumes it, or the grilling revealed it to be a duplicate — close that issue as
`superseded` instead of leaving it open with a cross-reference comment. The
reason is mandatory and is recorded as a comment on it:

```bash
python3 <issue-tracker-skill>/scripts/tracker.py set-status "<obsolete-id>" \
  superseded --reason "Subsumed by <new-main-id>, which specifies the same behavior."
```

`superseded` is reachable from every open state (not from `resolved`) and counts
as closed, so it no longer blocks its siblings. See the `issue-tracker` skill's
`reference/states.md`.

## 7. Hand off & stop

Tell the user the specification is complete and now lives in main-issue `<id>`
(`Type: <type>`), ready to be broken down. Then stop. Do **not** decompose it
into child-issues, generate an implementation plan, or write code: slicing the
PRD is the `issue-tracker` skill's decompose workflow, and it needs the user's
approval of the breakdown — a decision that stays in the main conversation.
