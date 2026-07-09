---
name: implement
description: Implements the open issues of the active feature sequentially using TDD (Test-Driven Development) at the agreed test seams.
user-invocable: false
---

# Implementation

Use this skill to systematically process the issues of the active feature.

## Workflow

### 1. Determine Active Feature
- Try to determine the active feature from the current conversation context.
- If unclear, read the file `.scratch/active-feature.txt` in the project root.
- If the file does not exist or is empty, ask the user for the slug of the feature.

### 2. Find Next Unblocked Issue
- Scan the directory `.scratch/<feature-slug>/issues/` for files:
    - Find the first open issue (numbered starting from `01`) that:
        - Has the status `Status: ready-for-agent`.
    - Is not blocked (i.e., all issues listed in `Blocked by:` have the status `Status: resolved`, or there are no blockers).
    - Change the status of the selected issue in the corresponding markdown file to `Status: claimed`.
    - Present the selected issue and its acceptance criteria to the user in the chat.
    - Stop scanning and ignore all other issues.
- During the subsequent implementation, only implement what was described in the found issue. Do not anticipate unimplemented issues in this ticket.

### 3. Perform TDD Cycle (Test-Driven Development)
If not already done, create a branch for the issue named `feature/<feature-slug>`, or check out this branch if it already exists. Implement the issue step by step in small units using TDD (Red-Green-Refactor). For each TDD step, perform the following:

1. **Red Phase**:
   - Write a failing test at the agreed test interface (seam) that verifies the desired behavior.
   - The test must make a meaningful assertion. Expected values must come from independent sources (literal, worked example, spec), not from the implementation itself (no tautological tests).
   - Run the test and verify that it is red (failing).
   
2. **Green Phase**:
   - Write code (strictly adhering to the guidelines in `CODE_GUIDELINES.md`) to make the failing test green (successful). Avoid speculative extensions or anticipating future tasks.
   - Run the test again and verify that it is green.
   
3. **Refactoring Phase**:
   - After a successful test run, the code can be cleaned up. (Note: Major architectural refactoring or code reviews take place outside of this loop during the testing phase).

*Determining the Test Command*:
- Read `.scratch/test-command.txt`.
- If not present, analyze the project root (e.g., `package.json` -> `npm test` or `vitest`; `Cargo.toml` -> `cargo test`; `requirements.txt` -> `pytest`).
- If it cannot be clearly determined, ask the user once for the command, execute it, and save it in `.scratch/test-command.txt`.

### 4. Resolve Issue
- As soon as all acceptance criteria of the issue are met and all tests pass successfully, update the issue file:
  - Set the status to `Status: resolved`.
  - Append a short summary of the solution under the heading `## Answer` (or `## Solution`).
- Make a git commit for the resolved issue on the local branch.

### 5. Completion (Handoff)
- Provide the user with a brief summary of the changes made and the status of the git repository.
