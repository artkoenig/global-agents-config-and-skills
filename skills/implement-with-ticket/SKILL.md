---
name: implement-with-ticket
description: Sequentially processes the open tickets/issues of the active feature from the local ticket workspace (`.scratch/` with an active feature), delegating the actual coding to the code-generation-principles. Use only when this local ticket/feature setup is present; for ad-hoc code changes without it, do not use this skill.
user-invocable: true
---

# Implementation (Ticket-Based)

Use this skill to systematically process the open issues of the active feature in the local ticket workspace.
Process the issues one after another; for each open issue, repeat steps 2–4.

## Workflow

### 1. Determine Active Feature
- Obtain the active feature slug by using the `/manage-feature` skill (action: `get-active`).
- If no active feature is set, ask the user to run `/manage-feature` to set it.

### 2. Find Next Unblocked Issue
- Find the next unblocked issue by using the `/manage-feature` skill (action: `next-issue`).
- Change the status of the selected issue to `claimed` by using the `/manage-feature` skill (action: `update-issue`).
- Present the selected issue and its acceptance criteria to the user in the chat.
- During the subsequent implementation, only implement what was described in the found issue. Do not anticipate unimplemented issues.

### 3. Implement the Issue
- If not already done, create a branch for the issue named `feature/<feature-slug>`, or check out this branch if it already exists.
- Implement the issue step by step in small, incremental units.
- For the actual coding, follow the `code-generation-principles` skill (meaningful names, SRP, comprehensive unit tests, etc.).
- After implementing, run the project's test suite and verify that all tests pass and the issue's acceptance criteria are met.

### 5. Completion (Handoff)
- Provide the user with a brief summary of the changes made and the status of the git repository.
