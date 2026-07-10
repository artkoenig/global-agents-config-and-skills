---
name: testing
description: Performs an agnostic three-axis verification of the current changes - Standards (static analysis plus code-smell review over the whole codebase), Specification (review of the diff against optional acceptance criteria), and Tests (running the local test suite).
user-invocable: true
---

# Testing and Verification

Use this skill to secure the current changes with a three-axis verification. Each axis answers a different question and operates on a different scope, so they run independently and in parallel:

- **Axis A - Standards** (`agents/standards.md`): "Is the code healthy?" Static analysis plus a code-smell review over the **entire codebase**.
- **Axis B - Specification** (`agents/specification.md`, optional): "Did we build the right thing?" Reviews the **diff** against a specification. Runs only when a specification source is available.
- **Axis C - Tests** (`agents/tests.md`): "Does it still work?" Runs the project's **test suite**.

The skill is agnostic - it works on any repository and does not depend on a specific feature/issue workspace or directory layout.

## Inputs (optional)

The skill runs with zero configuration. When invoked it may receive an optional argument (for example `/testing <acceptance-criteria-path>`):

- **acceptance-criteria** - a path to the acceptance criteria to verify against: a folder (e.g. a feature's `issues/` directory), a single spec/PRD file, or a ticket. When present it is passed to Axis B as the specification source and enables that axis; a folder is expanded to every acceptance-criteria file it contains.

The command inputs for the other two axes (the static-analysis command list and the test command) are discovered from the repository by convention (see the respective `agents/` file), so they need not be passed. The skill never hardcodes a project-specific directory.

## Workflow

### 1. Three-Axis Verification

Spawn one subagent per axis, in parallel, each following the corresponding file in `agents/`. Pass each subagent the inputs its file lists (repo root, the main branch, the per-axis command inputs it discovers, and - for Axis B - the **acceptance-criteria** path from the invocation, if one was given).

- Always run **Axis A (Standards)** and **Axis C (Tests)**.
- Run **Axis B (Specification)** only if a specification source is available - the **acceptance-criteria** argument, or otherwise a spec/PRD file, ticket, or path the user names. If none is found, skip it and note in the report that no specification was available.

### 2. Consolidation

- Present each subagent's report separately under its heading: `## Standards`, `## Specification` (if run), and `## Tests`.
- Summarize the result in one line: number of findings per axis, the most critical comment per axis, and whether the test suite is green.

### 3. Conclusion

- Ask the user if they want to make the recommended changes and refactorings (including fixing any failing tests or blocking analysis findings).
- If yes, execute the changes and refactorings, commit them, and run `/testing` again with the new state.
- If no (or if there are no findings), the verification is complete. Report the final green status of tests and analysis together with the review summary.

## Reference files

The `agents/` directory holds the detailed instructions for each axis subagent - read and pass along the relevant one when spawning that subagent:

- `agents/standards.md` - Axis A: static analysis gate + code-smell review over the whole codebase.
- `agents/specification.md` - Axis B: diff-vs-specification review (optional).
- `agents/tests.md` - Axis C: running the test suite.
