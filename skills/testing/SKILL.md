---
name: testing
description: Performs an agnostic three-axis verification of the current changes - Standards (static analysis plus code-smell review over the whole codebase), Specification (review of the diff against optional acceptance criteria), and Tests (running the local test suite).
user-invocable: true
---

# Testing and Verification

Use this skill to secure the current changes with a three-axis verification. Each axis answers a different question and operates on a different scope, so they run independently and in parallel. Each axis is a dedicated subagent, so its analysis, logs, and file reads never enter this conversation:

- **Axis A - Standards** (`standards-reviewer` subagent): "Is the code healthy?" Static analysis plus a code-smell review over the **entire codebase**.
- **Axis B - Specification** (`spec-reviewer` subagent, optional): "Did we build the right thing?" Reviews the **diff** against a specification. Runs only when a specification source is available.
- **Axis C - Tests** (`test-runner` subagent): "Does it still work?" Runs the project's **test suite**.

Each subagent carries its own model and tool restrictions, so the axes cost what they are worth: `opus` for the code-smell judgment of Axis A, `sonnet` for the diff-vs-spec comparison of Axis B, and `haiku` for running a command in Axis C. All three are read-only — they report, they never fix.

The skill is agnostic - it works on any repository and does not depend on a specific feature/issue workspace or directory layout. In the `issue-tracker` workflow it runs twice at different scopes: once per leaf issue, inside `issue-implementer`'s own worktree (see its Verify step) against that issue's acceptance criteria, and once more before resolving a **feature** (an issue with children) — see [resolve.md](../issue-tracker/workflows/resolve.md) step 2 — against the whole subtree's spec.

## Inputs (optional)

The skill runs with zero configuration. When invoked it may receive an optional argument (for example `/testing <acceptance-criteria-path>`):

- **acceptance-criteria** - a path to the acceptance criteria to verify against: a folder (e.g. a feature's `issues/` directory), a single spec/PRD file, or a ticket. When present it is passed to Axis B as the specification source and enables that axis; a folder is expanded to every acceptance-criteria file it contains.

The command inputs for the other two axes (the static-analysis command list and the test command) are discovered from the repository by convention (each subagent knows its own conventions), so they need not be passed. The skill never hardcodes a project-specific directory.

## Workflow

### 1. Three-Axis Verification

Spawn the three axis subagents **in parallel, in a single message**, passing each the inputs it expects (repo root, the main branch, and - for Axis B - the **acceptance-criteria** path from the invocation, if one was given). Each subagent's definition documents its own inputs.

- Always run **Axis A (Standards)** and **Axis C (Tests)**.
- Run **Axis B (Specification)** only if a specification source is available - the **acceptance-criteria** argument, or otherwise a spec/PRD file, ticket, or path the user names. If none is found, skip it and note in the report that no specification was available.

### 2. Consolidation

- Present each subagent's report separately under its heading: `## Standards`, `## Specification` (if run), and `## Tests`.
- Summarize the result in one line: number of findings per axis, the most critical comment per axis, and whether the test suite is green.

### 3. Conclusion

- Ask the user if they want to make the recommended changes and refactorings (including fixing any failing tests or blocking analysis findings).
- If yes, execute the changes and refactorings, commit them, and run `/testing` again with the new state.
- If no (or if there are no findings), the verification is complete. Report the final green status of tests and analysis together with the review summary.

## The axis subagents

Each axis is a subagent defined in `agents/` at the repository root of the
`artkoenig-skills` bundle, loaded from `~/.claude/agents/` (or under the
`artkoenig-skills:` prefix where the plugin is installed). Their definitions are
the single source of truth for what each axis does - do not restate their
instructions when spawning them, just pass the inputs:

| Axis | Subagent | Scope | Model |
| --- | --- | --- | --- |
| A - Standards | `standards-reviewer` | whole codebase | `opus` |
| B - Specification | `spec-reviewer` | the diff | `sonnet` |
| C - Tests | `test-runner` | the test suite | `haiku` |

If a subagent is unavailable in the current environment, say so rather than
inlining its work into this conversation - that would defeat the point of the
split.
