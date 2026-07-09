---
name: implement-all
description: Autonomously iterates through all open stories/features sequentially, implementing and testing them using subagents.
disable-model-invocation: true
---

# Implement All (Automated Feature Implementation Loop)

Use this skill to automatically analyze, implement, and test all open features of the project sequentially. This skill delegates the work for each feature/issue to specialized subagents that execute the existing skills (`requirements-analysis`, `implementation`, and `testing`).

## Workflow

### 1. Identify Features/Stories
- Read the global project PRD (typically `PRD.md` in the project root directory).
- Analyze the `## Features` section to extract all linked features and their corresponding paths (e.g., `.scratch/<feature-slug>/PRD.md`).
- If the global `PRD.md` does not exist or contains no entries, search for subdirectories in the `.scratch/` folder to determine the feature slugs.

### 2. Determine Open Features
Iterate through all found feature slugs and determine their status:
- Scan the directory `.scratch/<feature-slug>/issues/` for markdown files matching the pattern `NN-<slug>.md`.
- A feature is considered **open** (or incomplete) if at least one issue exists whose status is not `Status: resolved` (e.g., `Status: ready-for-agent` or `Status: claimed`).
- A feature is considered **completed** when all defined issues have the status `Status: resolved`. Features without issues are skipped, as it is assumed that the requirements analysis has already created issues.

### 3. Implement Features Sequentially
Go through all open features one by one. For each open feature, execute the following steps completely automatically:

#### Step A: Activate Feature & Prepare Branch
- Write the current feature slug into the file `.scratch/active-feature.txt` in the project root.
- Ensure that the git branch for the feature exists and is active. The branch name follows the pattern `feature/<feature-slug>`. If the branch does not exist, create it and check it out.

#### Step B: Spawn Subagents for Implementation & Testing
- Spawn a subagent for the active feature. The subagent receives the task:
  1. **Implementation**: Execute the `/implementation` skill. Go through all open issues of the feature one by one and implement them using TDD (Red-Green-Refactor) until all issues have the status `Status: resolved`.
  2. **Testing**: Immediately afterward, execute the `/testing` skill (run the complete test suite, type checking/linter, two-axis code review: Standards vs. Specification).
- If the subagent reports errors or gets stuck, interrupt the loop and inform the user.
- Ensure that the main branch is checked out and clean.

### 4. Completion (Handoff)
- Once all open features have been processed, present the user with a summary of the work performed:
  - List of all successfully implemented features.
  - Status of the git repository (current branch, clean working directory).
  - Confirmation that the entire test suite is green.
