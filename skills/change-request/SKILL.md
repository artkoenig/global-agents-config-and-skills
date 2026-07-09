---
name: change-request
description: Creates a new change request (feature or bug) in the project, adds it to the global PRD.md, and prepares the local workspace under .scratch/.
disable-model-invocation: true
---

# Add Change Request

Use this skill to add a new change request (feature or bug) to the project.

## Workflow

### 1. Request Change Request Information
- Interactively ask the user for the **name of the change request**, the **type (feature or bug)**, and a brief **description/purpose**.
- **Clarification for bugs**: If the change request is a bug, interactively ask the user for the **current behavior** (actual state) and the **expected behavior** (target state) to precisely clarify the error.
- Automatically generate a URL- and folder-compliant **change request slug** from the name (e.g., `authentication` or `data-export`, lowercase, hyphens instead of spaces, convert umlauts).
- **Existence and Status Check**:
  - Check if the change request already exists. A change request is considered existing if there is an entry in the global `PRD.md` under `## Features` or `## Change Requests`, or if the directory `.scratch/<change-request-slug>/` exists.
  - If the change request exists, determine its current status:
    - **Implemented**: All issues located in the directory `.scratch/<change-request-slug>/issues/` have the status `Status: resolved`.
    - **Planned**: The directory `.scratch/<change-request-slug>/` exists, but there are still open/unresolved issues, or no issues have been created yet.
  - If the change request has already been planned or implemented, inform the user of the found status and ask interactively how to proceed (e.g., choose a different name/slug, overwrite the existing workspace, or cancel the process).

### 2. Update Global PRD.md
- Locate the project-wide `PRD.md` in the project root.
- Add the new change request to the main `PRD.md` under the section `## Features` or `## Change Requests` as a list item:
  ```markdown
  - [Change Request Name](.scratch/<change-request-slug>/PRD.md): [Brief description]
  ```

### 3. Create Change Request Workspace
- Initialize the workspace by executing: `python3 .agents/skills/manage-feature/scripts/feature.py init <change-request-slug> "[Change Request Name]"` (replacing the placeholders with the actual slug and name).
- Open the newly created `.scratch/<change-request-slug>/PRD.md` and document the gathered information (Problem Statement, Solution, etc.).

### 4. Completion (Handoff)
- Do not generate an implementation plan (implementation_plan.md) and do not write code. Under no circumstances start with the implementation.
- Confirm to the user that the workspace for the change request `<change-request-slug>` has been successfully created.
- Automatically continue with the skill `/requirements-analysis`.
