---
name: requirements-analysis
description: Performs requirements analysis for the active feature, defines test interfaces (seams), completes the feature PRD, and breaks it down into local issues.
user-invocable: false
---

# Requirements Analysis

Use this skill to analyze the active feature in detail and break it down into implementable, testable tasks (issues).

## Workflow

### 1. Determine Active Feature
- Obtain the active feature slug by running `python3 .agents/skills/manage-feature/scripts/feature.py get-active`.
- If no active feature is set, ask the user to run `/manage-feature` to set it, or run `python3 .agents/skills/manage-feature/scripts/feature.py set-active <slug>` if you know the slug.

### 2. Context & Codebase Analysis
- Examine the current state of the code regarding the requirements. Use the domain documents present in the project (e.g., `CONTEXT.md`) and respect existing architectural decision records (ADRs).
- Identify affected classes, interfaces, APIs, data models, or UI components.

### 3. Grilling Session & Active Domain Modeling (the "grill-with-docs" principle)
- Relentlessly question the user on all aspects of the plan, requirements, and design to achieve a shared understanding.
- Go through each branch of the design tree and resolve dependencies between decisions sequentially.
- Ask questions **one at a time** and provide your **recommended answer** directly with each question. Wait for the user's feedback on each question before proceeding. (Asking multiple questions at once is confusing).
- If facts can be determined directly by exploring the codebase, research them independently instead of asking the user. The *decisions*, however, lie with the user – present them one by one.
- Perform **active domain modeling**:
  - Use and refine the domain model (Glossary in `CONTEXT.md` / `CONTEXT-MAP.md` and ADRs in `docs/adr/`) during the design.
  - If the user uses terms that conflict with the existing glossary in `CONTEXT.md`, point it out immediately ("The glossary defines 'X' as Y, but you seem to mean Z – which is correct?").
  - Question vague or overloaded terms and suggest precise designations (e.g., "You say 'Account' – do you mean the customer or the user?").
  - Discuss concrete scenarios and check them against the code to uncover contradictions.
  - Once a term is clarified, update the file `CONTEXT.md` directly inline (using the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)). The `CONTEXT.md` file should be free of implementation details (just a pure glossary).
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
