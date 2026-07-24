---
name: review
description: Performs an agnostic five-axis review of the current changes - Standards (static analysis plus code-smell review over the whole codebase), Specification (review of the diff against optional acceptance criteria), Tests (running the local test suite), Docs (review of the diff against the repository's documentation), and Design-Conformance (review of the diff against a design.md module plan; when none exists it falls back to a clean-room review that re-designs the solution from the problem and raw data alone).
user-invocable: true
---

# Review and Verification

Use this skill to secure the current changes with a five-axis review. Each axis answers a different question and operates on a different scope. Four of them always run as dedicated, read-only subagents whose analysis, logs and file reads never enter this conversation; the fifth (Design-Conformance) also runs as a read-only subagent when a design plan exists, and otherwise falls back to a clean-room review driven from this conversation, because that fallback runs a question/answer loop:

- **Axis A - Standards** (`standards-reviewer` subagent): "Is the code healthy?" Static analysis plus a code-smell review over the **entire codebase**.
- **Axis B - Specification** (`spec-reviewer` subagent, optional): "Did we build the right thing?" Reviews the **diff** against a specification. Runs only when a specification source is available.
- **Axis C - Tests** (`test-runner` subagent): "Does it still work?" Runs the project's **test suite**.
- **Axis D - Docs** (`docs-reviewer` subagent): "Is the documentation still consistent with what changed?" Reviews the **diff** against the repository's own documentation. Always runs; it needs no specification source. Its report is written in German by design.
- **Axis E - Design-Conformance** (`design-reviewer` subagent, with a `clean-room-review` fallback): "Did we build it the **way** we planned?" When a `design.md` module plan exists, `design-reviewer` reviews the **diff** against it — did the implementation honour the planned module boundaries and shared contracts? When there is **no** design plan (a single-slice main-issue, or a standalone `/review` on a repo with no plan), the axis falls back to the `clean-room-review` workflow: an external expert who never sees the code re-designs a solution from the problem and the **raw data alone**, reconciled against the implementation. Either way it always runs — the plan's soundness was already challenged by a clean-room gut-check *before* implementation, so here the plan-backed mode measures conformance to it.

Each subagent carries its own model and tool restrictions, so the axes cost what they are worth: `opus` for the code-smell judgment of Axis A, `sonnet` for the diff-vs-spec comparison of Axis B, `haiku` for running a command in Axis C, `sonnet` for the documentation-drift review of Axis D, and — for Axis E — `sonnet` for the `design-reviewer`'s diff-vs-plan comparison, or `opus` for the `clean-room-reviewer`'s independent design in the fallback. All are read-only — they report, they never fix (the `clean-room-reviewer` has no file tools at all).

The skill is agnostic - it works on any repository and does not depend on a specific issue workspace or directory layout. In the `issue-tracker` workflow it runs exactly once, before resolving a **main-issue** (an issue with children) — see [resolve.md](../issue-tracker/workflows/resolve.md) step 2 — against the whole subtree's spec. A child-issue's own `issue-implementer` Verify step runs only the test suite (via `test-runner`), not this full five-axis skill.

## Inputs (optional)

The skill runs with zero configuration. When invoked it may receive optional arguments (for example `/review <acceptance-criteria-path> [<design-plan-path>]`):

- **acceptance-criteria** - a path to the acceptance criteria to verify against: a folder (e.g. a feature's `issues/` directory), a single spec/PRD file, or a ticket. When present it is passed to Axis B as the specification source and enables that axis; a folder is expanded to every acceptance-criteria file it contains. It is also the primary source for **Axis E's clean-room fallback** problem statement (see below).
- **design-plan** - a path to the `design.md` module plan to check conformance against. When present, **Axis E** runs as `design-reviewer` against it. When absent (or the file no longer exists — the plan is temporary and is deleted at the resolution gate), Axis E falls back to the clean-room review. In the `issue-tracker` flow, resolve.md passes `docs/issues/<main-id>/design.md` here when the architect step produced one. If not passed explicitly, the skill may look for a `design.md` alongside the acceptance-criteria path.

The command inputs for the Standards and Tests axes (the static-analysis command list and the test command) are discovered from the repository by convention (each subagent knows its own conventions), so they need not be passed. The skill never hardcodes a project-specific directory. Axis E needs no configuration in its clean-room fallback either — this conversation assembles its brief.

## Workflow

### 1. Run the axes

Spawn **Axis A (Standards)**, **Axis C (Tests)**, **Axis D (Docs)** — plus **Axis B (Specification)** when a specification source is available, and **Axis E (Design-Conformance)** when a design plan is available — as subagents **in parallel, in a single message**, passing each the inputs it expects (repo root, the main branch, and - for Axis B - the **acceptance-criteria** path, and - for Axis E - the **design-plan** path). Each subagent's definition documents its own inputs.

- Always run **Axis A**, **Axis C**, and **Axis D**. Axis D always runs — it compares the diff against the repository's own documentation and so needs no specification source.
- Run **Axis B** only if a specification source is available - the **acceptance-criteria** argument, or otherwise a spec/PRD file, ticket, or path the user names. If none is found, skip it and note in the report that no specification was available.
- **Axis E always runs, in one of two modes:**
  - **Design-Conformance (preferred):** if a **design-plan** (`design.md`) is available, spawn the `design-reviewer` subagent against it — in the same parallel batch as A/B/C/D, since it is a fire-and-forget diff-vs-plan review with no question/answer loop.
  - **Clean-Room (fallback):** if there is **no** design plan, Axis E instead runs the `clean-room-review` workflow, whose question/answer loop this conversation drives from the real code — so it is *not* part of the parallel batch. Kick off the parallel axes first, then carry out the fallback as described next.

#### Axis E fallback — assemble the brief, then run clean-room-review

This runs **only when no design plan was available** (with a plan, `design-reviewer` above has already covered Axis E). First assemble a **neutral brief** for the `clean-room-reviewer` containing exactly these three parts and nothing more:

1. **Big picture** — one or two sentences on what the application is and the problem it exists to solve, so the reviewer knows the domain it is designing for.
2. **Problem** — what this change must achieve. Take it from the **issue description** (the acceptance-criteria / issue source) when one is available; otherwise derive it from this conversation.
3. **Base data & its shape** — the raw data the system works with and its form (tree structure, SQL database, graph, event stream, files, …). The reviewer needs this factual substrate to base its design on.

Discipline that makes this axis worth running:

- **Pass only the raw ("base") data and its shape.** Do **not** put derived domain data, the domain model, or any domain logic into the brief — those are exactly what this axis exists to have re-derived and, where warranted, challenged. If our own domain modeling leaks into the brief, the reviewer merely ratifies it and the axis is worthless.
- **In the Q&A loop, answer the reviewer's questions from the real code and domain — status quo only, no steering.** Sharing domain knowledge **is allowed when the reviewer explicitly asks for it**: the withholding applies to the proactive brief, not to honest answers to direct questions. Reflect *what is*, never nudge toward the solution we already built.

Then run the [`clean-room-review`](../clean-room-review/SKILL.md) workflow with that brief: derive the reviewer's role, spawn `clean-room-reviewer`, run its question/answer loop (recording every Q&A pair in a table), and **synthesize its blind proposal against the actual implementation**. The synthesis classifies each point as one of:

- **Confirmed** — the independent design agrees with what we built; independent evidence the approach is sound.
- **Better** — the independent design improves on the implementation or its domain modeling; a change worth making.
- **Impractical** — the proposal is ruled out by a real constraint the blind reviewer could not see; name the constraint.

### 2. Consolidation

- Present each axis's report separately under its heading: `## Standards`, `## Specification` (if run), `## Tests`, `## Docs`, and — for Axis E — `## Design-Conformance` when `design-reviewer` ran, or `## Clean-Room` when the fallback ran. The `## Docs` section is the `docs-reviewer`'s German report verbatim, and it is always present — showing either the documentation drift it found or that nichts gefunden wurde. The `## Design-Conformance` section shows the conformance verdict and the notable departures (drift-to-fix vs justified-improvement); the `## Clean-Room` fallback section shows the Q&A table and the reconciled proposal (Confirmed / Better / Impractical).
- Summarize the result in one line: number of findings per axis (including Docs and Axis E), the most critical comment per axis, and whether the test suite is green.

### 3. Conclusion

- Ask the user if they want to make the recommended changes and refactorings (including fixing any failing tests or blocking analysis findings).
- If yes, execute the changes and refactorings, commit them, and run `/review` again with the new state.
- If no (or if there are no findings), the verification is complete. Report the final green status of tests and analysis together with the review summary.

## The axis subagents

Each axis is a subagent defined in `agents/` at the repository root of
[global-agents-config-and-skills](https://github.com/artkoenig/global-agents-config-and-skills),
loaded into `~/.claude/agents/` by the `cloud-session-bootstrap` SessionStart
hook (a direct git clone + symlink, not a plugin install — there is no plugin
marketplace anymore). Their definitions are the single source of truth for
what each axis does - do not restate their instructions when spawning them,
just pass the inputs:

| Axis | Subagent | Scope | Model |
| --- | --- | --- | --- |
| A - Standards | `standards-reviewer` | whole codebase | `opus` |
| B - Specification | `spec-reviewer` | the diff | `sonnet` |
| C - Tests | `test-runner` | the test suite | `haiku` |
| D - Docs | `docs-reviewer` | the diff | `sonnet` |
| E - Design-Conformance | `design-reviewer` (with `clean-room-review` fallback) | the diff vs the `design.md` plan; or, with no plan, an independent design from problem + raw data reconciled against the diff | `sonnet` / `opus` |

Axes A–D are spawned directly and in parallel. **Axis E in its Design-Conformance
mode** (`design-reviewer`, when a `design.md` exists) is also a parallel
fire-and-forget subagent. **Axis E's clean-room fallback** (when no plan exists)
is driven through the `clean-room-review` skill/workflow instead — the
`clean-room-reviewer` has no file tools and never sees the repository, so this
conversation must run its question/answer loop and do the reconciliation.

If a subagent is unavailable in the current environment, say so rather than
inlining its work into this conversation - that would defeat the point of the
split. For the Axis E clean-room fallback specifically, a reviewer that could see
the code would not be a clean room, so never role-play it yourself.
