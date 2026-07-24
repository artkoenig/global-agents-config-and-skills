---
name: review
description: Performs an agnostic five-axis review of the current changes - Standards (static analysis plus code-smell review over the whole codebase), Specification (review of the diff against optional acceptance criteria), Tests (running the local test suite), Docs (review of the diff against the repository's documentation), and Design-Conformance (review of the diff against a design.md module plan, when one exists).
user-invocable: true
---

# Review and Verification

Use this skill to secure the current changes with a five-axis review. Each axis answers a different question and operates on a different scope. All of them run as dedicated, read-only subagents whose analysis, logs and file reads never enter this conversation — fire-and-forget, with no question/answer loop; two of them (Specification and Design-Conformance) run only when their source is available:

- **Axis A - Standards** (`standards-reviewer` subagent): "Is the code healthy?" Static analysis plus a code-smell review over the **entire codebase**.
- **Axis B - Specification** (`spec-reviewer` subagent, optional): "Did we build the right thing?" Reviews the **diff** against a specification. Runs only when a specification source is available.
- **Axis C - Tests** (`test-runner` subagent): "Does it still work?" Runs the project's **test suite**.
- **Axis D - Docs** (`docs-reviewer` subagent): "Is the documentation still consistent with what changed?" Reviews the **diff** against the repository's own documentation. Always runs; it needs no specification source. Its report is written in German by design.
- **Axis E - Design-Conformance** (`design-reviewer` subagent, optional): "Did we build it the **way** we planned?" Reviews the **diff** against a `design.md` module plan — did the implementation honour the planned module boundaries and shared contracts? Runs only when a design plan is available (e.g. a multi-slice main-issue where the architect step produced one); with no plan it is skipped, like Axis B without a spec. The plan's soundness was already challenged by a clean-room gut-check in the architect workflow *before* implementation, so here Axis E just measures conformance to it.

Each subagent carries its own model and tool restrictions, so the axes cost what they are worth: `opus` for the code-smell judgment of Axis A, `sonnet` for the diff-vs-spec comparison of Axis B, `haiku` for running a command in Axis C, `sonnet` for the documentation-drift review of Axis D, and `sonnet` for the diff-vs-plan comparison of Axis E. All are read-only — they report, they never fix.

The skill is agnostic - it works on any repository and does not depend on a specific issue workspace or directory layout. In the `issue-tracker` workflow it runs exactly once, before resolving a **main-issue** (an issue with children) — see [resolve.md](../issue-tracker/workflows/resolve.md) step 2 — against the whole subtree's spec. A child-issue's own `issue-implementer` Verify step runs only the test suite (via `test-runner`), not this full five-axis skill.

## Inputs (optional)

The skill runs with zero configuration. When invoked it may receive optional arguments (for example `/review <acceptance-criteria-path> [<design-plan-path>]`):

- **acceptance-criteria** - a path to the acceptance criteria to verify against: a folder (e.g. a feature's `issues/` directory), a single spec/PRD file, or a ticket. When present it is passed to Axis B as the specification source and enables that axis; a folder is expanded to every acceptance-criteria file it contains.
- **design-plan** - a path to the `design.md` module plan to check conformance against. When present, **Axis E** runs as `design-reviewer` against it. When absent (or the file no longer exists — the plan is temporary and is deleted at the resolution gate), Axis E is skipped. In the `issue-tracker` flow, resolve.md passes `docs/issues/<main-id>/design.md` here when the architect step produced one. If not passed explicitly, the skill may look for a `design.md` alongside the acceptance-criteria path.

The command inputs for the Standards and Tests axes (the static-analysis command list and the test command) are discovered from the repository by convention (each subagent knows its own conventions), so they need not be passed. The skill never hardcodes a project-specific directory.

## Workflow

### 1. Run the axes

Spawn **Axis A (Standards)**, **Axis C (Tests)**, **Axis D (Docs)** — plus **Axis B (Specification)** when a specification source is available, and **Axis E (Design-Conformance)** when a design plan is available — as subagents **in parallel, in a single message**, passing each the inputs it expects (repo root, the main branch, and - for Axis B - the **acceptance-criteria** path, and - for Axis E - the **design-plan** path). Each subagent's definition documents its own inputs.

- Always run **Axis A**, **Axis C**, and **Axis D**. Axis D always runs — it compares the diff against the repository's own documentation and so needs no specification source.
- Run **Axis B** only if a specification source is available - the **acceptance-criteria** argument, or otherwise a spec/PRD file, ticket, or path the user names. If none is found, skip it and note in the report that no specification was available.
- Run **Axis E** only if a **design-plan** (`design.md`) is available. When present, `design-reviewer` reviews the diff against it in the same parallel batch as A/B/C/D — it is a fire-and-forget diff-vs-plan review with no question/answer loop. When absent, skip Axis E and note in the report that no design plan was available (exactly as Axis B is skipped without a spec). There is no clean-room fallback here — the plan's soundness was already challenged by the clean-room gut-check in the architect workflow, *before* implementation.

### 2. Consolidation

- Present each axis's report separately under its heading: `## Standards`, `## Specification` (if run), `## Tests`, `## Docs`, and `## Design-Conformance` (if run). The `## Docs` section is the `docs-reviewer`'s German report verbatim, and it is always present — showing either the documentation drift it found or that nichts gefunden wurde. The `## Design-Conformance` section shows the conformance verdict and the notable departures (drift-to-fix vs justified-improvement).
- Summarize the result in one line: number of findings per axis (including Docs, and Axis E if it ran), the most critical comment per axis, and whether the test suite is green.

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
| E - Design-Conformance | `design-reviewer` (when a `design.md` exists) | the diff vs the `design.md` plan | `sonnet` |

All axes are spawned directly and in parallel, in a single message —
`design-reviewer` (Axis E) among them whenever a `design.md` is available. There
is no question/answer loop and no clean-room step in this skill; the independent
clean-room design happens once in the architect workflow, on the plan, before
implementation.

If a subagent is unavailable in the current environment, say so rather than
inlining its work into this conversation - that would defeat the point of the
split.
