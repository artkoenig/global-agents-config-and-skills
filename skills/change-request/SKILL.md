---
name: change-request
description: Creates or analyzes a change request (feature or bug), performs requirements analysis, completes the feature PRD, and breaks it down into local issues.
user-invocable: true
---

# Change Request & Requirements Analysis

Use this skill to either add a new change request to the project or deeply analyze an existing one to break it down into implementable tasks (issues).

## Workflow

### 1. Determine Action (New vs. Existing)
- Determine if the user wants to create a **new** change request or analyze an **existing** one.
- **If new:**
  - Interactively ask the user for the **name**, **type (feature or bug)**, and a brief **description**. (For bugs: ask for current vs. expected behavior).
  - Generate a slug.
  - Initialize the workspace by using the `/manage-feature` skill (action: `init`, passing the slug and name).
  - Update the global `PRD.md` in the project root by adding the new change request under `## Features` or `## Change Requests`:
    `- [Change Request Name](.scratch/<slug>/PRD.md): [Brief description]`
- **If existing:**
  - Obtain the active feature slug by using the `/manage-feature` skill (action: `get-active`).
  - If no active feature is set, ask the user to set it, or use the `/manage-feature` skill (action: `set-active`) if you know the slug.

### 2. Context & Codebase Analysis
- Examine the current state of the code regarding the requirements. Use the domain documents present in the project (e.g., `CONTEXT.md`) and respect existing architectural decision records (ADRs).
- Identify affected classes, interfaces, APIs, data models, or UI components.

### 3. Grilling Session & Active Domain Modeling (the "grill-with-docs" principle)
- Relentlessly question the user on all aspects of the plan, requirements, and design to achieve a shared understanding.
- Go through each branch of the design tree and resolve dependencies between decisions sequentially.
- Ask questions **one at a time** and provide your **recommended answer** directly with each question. Wait for the user's feedback on each question before proceeding.
- If facts can be determined directly by exploring the codebase, research them independently instead of asking the user.
- Perform **active domain modeling**:
  - Use and refine the domain model (Glossary in `CONTEXT.md` / `CONTEXT-MAP.md` and ADRs in `docs/adr/`) during the design.
  - If the user uses terms that conflict with the existing glossary in `CONTEXT.md`, point it out immediately.
  - Question vague or overloaded terms and suggest precise designations.
  - Discuss concrete scenarios and check them against the code to uncover contradictions.
  - Once a term is clarified, update the file `CONTEXT.md` directly inline (using the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)). The `CONTEXT.md` file should be free of implementation details.
  - Propose/create ADRs under `docs/adr/` (using the format in [ADR-FORMAT.md](./ADR-FORMAT.md)) sparingly and only if all three criteria are met:
    1. The decision is hard to reverse.
    2. The decision is surprising to future readers without context.
    3. The decision results from a real trade-off (genuine alternatives).
- Only proceed when the user has confirmed that a shared understanding of the model and design has been achieved.

### 4. Define Test Interfaces (Seams)
- Plan at which public interfaces (seams) the feature should be tested. Prefer existing interfaces and keep the number of new interfaces as low as possible.
- Present the proposed interfaces to the user in the chat for approval. Do not write tests before the test interfaces are agreed upon.

### 5. Complete Feature PRD
- Synthesize the findings from the discussion and codebase analysis and complete the file `.scratch/<feature-slug>/PRD.md` (e.g., problem statement, solution, user stories, technical decisions like data structures or API contracts, as well as the test interfaces).
- Do **not** conduct another interview with the user for this – instead, use the knowledge already acquired in step 3.

### 6. Break Down into Vertical Issues (Tracer Bullets)
- Break the feature down into independently workable tasks (issues).
- Use the principle of **vertical slices (tracer bullets)**: Each task cuts through all affected layers (e.g., schema, API, UI, tests) and delivers a minimal, independently demonstrable, and verifiable behavior. Prefactoring tasks should be defined as the first issues.
- Present the list of issues to the user in the chat. For each issue, show:
  - **Title**: A short, concise name
  - **Blocked by**: Other issues that must be completed first
  - **User Stories**: Which user story(ies) this covers
- Ask the user:
  - Is the granularity appropriate?
  - Are the dependencies correct?
  - Should tasks be merged or further split?
- Once the user approves the breakdown, create a file for each issue under `.scratch/<feature-slug>/issues/NN-<slug>.md` (numbered starting from `01`), using the following structure:
  ```markdown
  Status: ready-for-agent
  Type: task
  Blocked by: [List of NN, or "None"]

  ## Parent
  Reference to the Feature PRD: `.scratch/<feature-slug>/PRD.md`

  ## What to Build
  [Short, precise description of the end-to-end behavior. Avoid concrete file paths, as they become outdated quickly.]

  ## Acceptance Criteria
  - [ ] Criterion 1
  - [ ] Criterion 2

  ## Comments
  *Feedback and notes during implementation can be appended here.*
  ```

### 7. Completion (Handoff)
- Do not generate an implementation plan (implementation_plan.md) and do not write code. Under no circumstances start with the implementation.
- Inform the user that the requirements analysis is complete.
- Advise the user that they can now run the `/implement-all` command to start the implementation of the feature/CR.
