---
name: new-project
description: Initializes a new local project, asks for the vision/description, clarifies the scope, and creates the project-wide PRD.md as well as local issue tracking structures.
disable-model-invocation: true
---

# Initialize New Project

Use this skill to set up a new project on your local machine.

## Workflow

### 1. Gather Project Metadata
- Interactively ask the user for the **name** of the project.
- Ask for a brief **description** of the vision and main goal of the project.
- Conduct a short interview on the **scope** (What should the project be able to do? What is out of scope?).

### 2. Initialize Git
- Check in the current working directory if a git repository already exists (e.g., via `git status` or the presence of `.git`).
- If not, initialize it by executing `git init`.
- Ensure the project's `.gitignore` contains an entry for `.scratch/` (transient agent working files such as `.scratch/analysis.md` must not be committed). Create `.gitignore` if it does not exist, and append the `.scratch/` entry only if it is not already present.

### 3. Create Directory Structure & Configurations
- Create the `docs/features/` directory in the project root directory.
- Configure local issue tracking automatically and silently by creating the following configuration files:
  
  - **`docs/agents/issue-tracker.md`**:
    ```markdown
    # Issue tracker: Local Markdown
    Issues and PRDs for this repo are located as markdown files under `docs/features/`.
    ```
    
  - **`docs/agents/triage-labels.md`**:
    ```markdown
    # Triage label vocabulary
    - `needs-triage` — For evaluation by the maintainer
    - `needs-info` — Waiting for feedback
    - `ready-for-agent` — Fully specified, ready for automatic implementation (AFK)
    - `claimed` — In progress by the agent
    - `resolved` — Successfully implemented and resolved
    ```
    
  - **`docs/agents/domain.md`**:
    ```markdown
    # Domain docs layout
    Single-context layout. The domain description is located in `CONTEXT.md` at the project root.
    ```

- Look for `CLAUDE.md` or `AGENTS.md` in the project root. 
  - If either exists, insert or update the section `## Agent skills` (if not present) within it.
  - If neither exists, briefly ask the user which file should be created, and create it.
  
  Insert the following block:
  ```markdown
  ## Agent skills

  ### Issue tracker
  Local markdown tracking under `docs/features/`. See `docs/agents/issue-tracker.md`.

  ### Triage labels
  Local status labels. See `docs/agents/triage-labels.md`.

  ### Domain docs
  Single-context layout. See `docs/agents/domain.md`.
  ```

### 4. Create Project PRD
- Create an initial `PRD.md` directly in the main directory of the project (project root) with the following structure:
  ```markdown
  # PRD: [Project Name]

  ## Vision & Description
  [Insert the captured vision/description here]

  ## Scope
  [Summary of the scope decisions]

  ## Change Requests
  *Change requests will be automatically entered here by the `/change-request` command.*
  ```

### 5. Completion (Handoff)
- Inform the user that the project has been successfully initialized for the local workflow.
- Point out that they can now invoke the `/change-request` command to create the first change request.
