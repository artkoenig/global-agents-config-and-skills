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
- Create the directory `.scratch/<change-request-slug>/` as well as the subdirectory `.scratch/<change-request-slug>/issues/`.
- Write the current slug into the status file `.scratch/active-feature.txt` (overwrite any existing old slugs):
  ```
  <change-request-slug>
  ```
- Create a PRD template under `.scratch/<change-request-slug>/PRD.md` with the following sections (adjust the description if it is a bug):
  ```markdown
  # PRD: [Change Request Name]

  ## Problem Statement / Bug Description
  [Describe the problem the user is having or how the bug manifests here. If a bug: document Current Behavior vs. Expected Behavior]

  ## Solution
  [The proposed solution from the user's perspective]

  ## User Stories / Requirements
  1. As an <Actor>, I want <Feature>, in order to achieve <Benefit>.

  ## Technical Decisions
  - Affected Modules:
  - Technical Clarifications/Architectural Decisions:
  - API Contracts / Data Models:

  ## Testing Decisions
  - Modules to Test:
  - Test Interfaces (Seams):

  ## Out of Scope
  - [Things that are not part of this change request]
  ```

### 4. Completion (Handoff)
- Do not generate an implementation plan (implementation_plan.md) and do not write code. Under no circumstances start with the implementation.
- Confirm to the user that the workspace for the change request `<change-request-slug>` has been successfully created.
- Automatically continue with the skill `/requirements-analysis`.
