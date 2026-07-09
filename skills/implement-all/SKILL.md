---
name: implement-all
description: Autonomously iterates through all open stories/features sequentially, implementing and testing them using subagents.
disable-model-invocation: true
---

# Implement All (Automated Feature Implementation Loop)

Use this skill to automatically analyze, implement, and test all open features of the project sequentially. This skill delegates the work for each feature/issue to specialized subagents that execute the existing skills (`requirements-analysis`, `implement`, and `testing`).

## Workflow

### 1. Identify Open Features
- Run `python3 .agents/skills/manage-feature/scripts/feature.py list-open-features` to get a list of all features that have at least one unresolved issue.
- If no open features are found, the process is complete.

### 2. Implement Features Sequentially
Go through all open features one by one. For each open feature, execute the following steps completely automatically:

#### Step A: Activate Feature & Prepare Branch
- Set the current feature as active by running `python3 .agents/skills/manage-feature/scripts/feature.py set-active <feature-slug>`.
- Ensure that the git branch for the feature exists and is active. The branch name follows the pattern `feature/<feature-slug>`. If the branch does not exist, create it and check it out.

#### Step B: Spawn Subagents for Implementation & Testing
- Spawn a subagent for the active feature. The subagent receives the task:
  1. **Implementation**: Execute the `/implement` skill. Go through all open issues of the feature one by one and implement them using TDD (Red-Green-Refactor) until all issues have the status `Status: resolved`.
  2. **Testing**: Immediately afterward, execute the `/testing` skill (run the complete test suite, type checking/linter, two-axis code review: Standards vs. Specification).
- If the subagent reports errors or gets stuck, interrupt the loop and inform the user.
- Ensure that the main branch is checked out and clean.

### 4. Completion (Handoff)
- Once all open features have been processed, present the user with a summary of the work performed:
  - List of all successfully implemented features.
  - Status of the git repository (current branch, clean working directory).
  - Confirmation that the entire test suite is green.
