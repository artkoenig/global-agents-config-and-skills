---
name: testing
description: Runs final tests and static analysis for the active feature and initiates a local two-axis code review (Standards vs. Specification).
user-invocable: true
---

# Testing and Verification

Use this skill to finally secure the implementation of a feature, run the entire local test suite, and perform a code review.

## Workflow

### 1. Determine Active Feature
- Obtain the active feature slug by using the `/manage-feature` skill (action: `get-active`).
- If no active feature is set, ask the user to run `/manage-feature` to set it.

### 2. Run Local Test Suite & Static Analysis
- Determine the test command:
  - Read `.scratch/test-command.txt`.
  - If not present, analyze the files in the project root (e.g., presence of `package.json` -> `npm test` or `vitest`; `Cargo.toml` -> `cargo test`; `requirements.txt` -> `pytest`).
  - If it cannot be clearly determined, ask the user once for the test command and save it in `.scratch/test-command.txt`.
- Execute the test command and ensure that **all** tests of the project pass successfully (are green).
- Determine the static-analysis command(s):
  - Read `.scratch/analysis-command.txt`. It may contain one command per line (for example a linter and a separate architecture check).
  - If the file is absent, the project has no configured static analysis - skip this step and do not assume any specific tool.
- Run each configured analysis command as a gate:
  - Write the combined output to `.scratch/analysis/latest.md` (create the folder if absent) so the results are available tool-agnostically.
  - A non-zero exit code is a **blocking** failure and must be resolved before proceeding, exactly like a failing test. Findings that do not fail the command (advisory) are recorded in the report but do not block.

### 3. Two-Axis Code Review
Conduct a review of the changes that were made as part of the feature.

- **Determine Diff Base Point**:
  - Check if the branch `feature/<feature-slug>` exists and if you have checked it out as your current branch. Switch to it if necessary. If that is not possible, abort the skill and output an error message.
  - Determine the merge base of the current changes against the main branch (default `main` or `master` via `git merge-base main HEAD`). If `main`/`master` do not exist or are unclear, ask the user for the comparison branch or commit.
  - Run `git diff <merge-base>...HEAD` to capture the changes.

Spawn two parallel subagents to independently review the diff along two axes:

#### Axis A: Standards (Coding Guidelines & Code Smells)
The Standards subagent checks the diff against the project's coding guidelines in effect (do not assume a specific filename) as well as against the following heuristics for code smells:
- **Mysterious Name**: Unclear function, variable, or type names.
- **Duplicated Code**: Identical or very similar logic structures across multiple lines/files.
- **Feature Envy**: A method accesses the data of another object more than its own.
- **Data Clumps**: Groups of data fields that always appear together (might want to be their own type).
- **Primitive Obsession**: Using primitives instead of a dedicated type for domain concepts.
- **Divergent Change**: One file/class is modified for many different reasons.
- **Shotgun Surgery**: One logical change forces scattered adjustments across many files.
- **Speculative Generality**: Abstract classes, parameters, or hooks that are not needed for the current specification.

*Rules for Standards*: The project's documented guidelines override the smell heuristics. Smells already covered by the Step 2 static-analysis gate - typically Duplicated Code, unclear names, magic numbers, and over-long or over-complex functions - are considered handled; do not re-report them. Concentrate on the judgment smells an automated gate cannot detect (Feature Envy, Divergent Change, Shotgun Surgery, Speculative Generality). Use the analysis report in `.scratch/analysis/` as input.

#### Axis B: Specification (Spec)
The Spec subagent compares the diff with the feature PRD located at `.scratch/<feature-slug>/PRD.md`:
- **Missing Requirements**: Which requirements described in the PRD were not implemented or only partially implemented?
- **Scope Creep**: What changes were implemented that the PRD didn't ask for at all?
- **Flawed Logic**: Where does the implementation look faulty or deviate from the specifications?

#### Consolidation
- Present the reports of both subagents separately under the headings `## Standards` and `## Specification`.
- Summarize the result in one line (number of findings per axis as well as the most critical comment per axis).

### 4. Conclusion
- Ask the user if they want to make the recommended changes and refactorings.
- If yes, execute the changes and refactorings and commit them. Run `/testing` again with the new state.
- If no, or if no changes are recommended AND all issues of this feature have the status `resolved`, use the `/manage-feature` skill (action: `complete`) to clear the active feature. 
- Offer the user to push the feature branch to the remote repository and generate a Pull Request Description based on the PRD.