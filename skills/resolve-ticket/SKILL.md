---
name: resolve-ticket
description: Marks an already-implemented and tested issue/ticket of the active feature as resolved, by setting its status to resolved and appending a short solution summary. Use only after the implementation is complete and all tests pass.
disable-model-invocation: true
---

# Resolve Ticket

Use this skill to mark a single issue of the active feature as resolved, once it has been fully implemented and all its tests pass.

## Workflow

- Set the status to `Status: resolved` by using the `/manage-feature` skill (action: `update-issue`).
- Append a short summary of the solution under the heading `## Answer` (or `## Solution`).
