---
name: testing
description: Runs the local test suite and static analysis for the current changes and performs an agnostic two-axis code review (Standards and, if a specification is provided, Specification).
user-invocable: true
---

# Testing and Verification

Use this skill to secure the current changes: run the entire local test suite, run static analysis, and perform a code review of the diff. The skill is agnostic - it works on any repository and does not depend on a feature/issue workspace.

## Workflow

### 1. Run Local Test Suite & Static Analysis
- Determine the test command:
  - Read `.scratch/test-command.txt` if it exists.
  - If not present, analyze the files in the project root (e.g., presence of `package.json` -> `npm test` or `vitest`; `Cargo.toml` -> `cargo test`; `requirements.txt` -> `pytest`).
  - If it cannot be clearly determined, ask the user once for the test command and save it in `.scratch/test-command.txt`.
- Execute the test command and ensure that **all** tests of the project pass successfully (are green). A failing test is a **blocking** failure: report the failing output and resolve it (or ask the user how to proceed) before continuing.
- Determine the static-analysis command(s):
  - Read `.scratch/analysis-command.txt` if it exists. It may contain one command per line (for example a linter and a separate architecture check).
  - If the file is absent, the project has no configured static analysis - skip this step and do not assume any specific tool.
- Run each configured analysis command as a gate:
  - Write the combined output to `.scratch/analysis/latest.md` (create the folder if absent) so the results are available tool-agnostically.
  - A non-zero exit code is a **blocking** failure and must be resolved before proceeding, exactly like a failing test. Findings that do not fail the command (advisory) are recorded in the report but do not block.

### 2. Two-Axis Code Review
Conduct a review of the current changes.

- **Determine Diff Base Point**:
  - Determine the merge base of the current branch against the main branch (default `main` or `master` via `git merge-base main HEAD`). If `main`/`master` do not exist or are unclear, ask the user for the comparison branch or commit.
  - Run `git diff <merge-base>` to capture the changes. This intentionally includes both committed branch changes and the uncommitted working tree, so the review covers the full current state.

Spawn subagents to independently review the diff along the following axes:

#### Axis A: Standards (Coding Guidelines & Code Smells)
The Standards subagent checks the diff against the project's coding guidelines in effect (do not assume a specific filename) as well as against the following heuristics for code smells:
- **Mysterious Name**: Unclear function, variable, or type names.
- **Duplicated Code**: Identical or very similar logic structures across multiple lines/files.
- **Feature Envy**: A method accesses the data of another object more than its own.
- **Data Clumps**: Groups of data fields that always appear together (might want to be their own type).
- **Primitive Obsession**: Using primitives instead of a dedicated type for domain concepts.
- **Divergent Change**: One file/class is modified for many different reasons.
- **Shotgun Surgery**: One logical change forces scattered adjustments across many files.
- **Speculative Generality**: Abstract classes, parameters, or hooks that are not needed for the current change.

*Rules for Standards*: The project's documented guidelines override the smell heuristics. Smells already covered by the Step 1 static-analysis gate - typically Duplicated Code, unclear names, magic numbers, and over-long or over-complex functions - are considered handled; do not re-report them. Concentrate on the judgment smells an automated gate cannot detect (Feature Envy, Divergent Change, Shotgun Surgery, Speculative Generality). Use the analysis report in `.scratch/analysis/` as input if present.

#### Axis B: Specification (optional)
This axis only runs if a specification source is available. A specification is any document describing what the change is supposed to do (e.g., a spec/PRD file, a ticket, or a path the user provides when invoking the skill).
- If no specification source is provided or found, **skip this axis** and note in the report that no specification was available.
- If a specification source is available, the Spec subagent compares the diff against it:
  - **Missing Requirements**: Which requirements described in the specification were not implemented or only partially implemented?
  - **Scope Creep**: What changes were implemented that the specification didn't ask for at all?
  - **Flawed Logic**: Where does the implementation look faulty or deviate from the specification?

#### Consolidation
- Present the reports of the subagents separately under the headings `## Standards` and (if run) `## Specification`.
- Summarize the result in one line (number of findings per axis as well as the most critical comment per axis).

### 3. Conclusion
- Ask the user if they want to make the recommended changes and refactorings.
- If yes, execute the changes and refactorings, commit them, and run `/testing` again with the new state.
- If no (or if there are no findings), the review is complete. Report the final green status of tests and analysis together with the review summary.
