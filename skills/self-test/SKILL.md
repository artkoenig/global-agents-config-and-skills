---
name: self-test
description: The self-testing apparatus for this repo's own workflow rules. Use it to run the determinisitic git checks and the behavioral evals that verify skills, subagents, and AGENTS.md rules actually behave as documented. Trigger on phrases like "run the self-test skill", "run behavioral evals", "check the git rules", or "run the tests".
user-invocable: true
---

# Self-Test Skill

This repo's `AGENTS.md`, skills, and subagents govern how Claude Code works. This skill is how those rules are kept honest: every rule is bound to a test.

There are two kinds of tests in this repository:
1. **Deterministic checks**: Instant, no-LLM checks run via `python3 -m unittest discover -s scripts -p 'test_*.py'`. These also run in the `pre-push` git hook.
2. **Behavioral evals**: Slower, full-agentic workflows that verify whether skills/rules actually behave as documented. Since they require headless agent executions, they are run entirely via this skill.

## Running the Deterministic Checks
When asked to run the tests, first execute the deterministic checks using the shell:
```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

## Running the Behavioral Evals
The behavioral evals are defined in `evals.json` files scattered throughout the repo. To run them, you will spawn subagents for execution and grading.

### 1. Discovery
The following 15 behavioral eval scenarios are currently defined across 11 files:
1. **Investigation stays read-only** (`evals/agents-md/investigate-means-read-only/evals.json`)
2. **Trivial doc edit isn't over-tracked** (`evals/agents-md/trivial-change-not-over-tracked/evals.json`)
3. **Bug reproduced end-to-end before fixing** (`evals/agents-md/reproduce-bug-e2e-first/evals.json`)
4. **Non-trivial code change asks before editing** (`evals/agents-md/ask-before-code-changes/evals.json`)
5. **Direct non-trivial edits happen in an isolated worktree** (`evals/agents-md/worktree-isolation/evals.json`)
6. **Code-health review delegated to standards-reviewer** (`agents/standards-reviewer/evals/evals.json`)
7. **Test run delegated to the test-runner subagent** (`agents/test-runner/evals/evals.json`)
8. **Vague feature triggers spec grilling**, and **a pre-baked solution is not transcribed into the spec** (`skills/grill-me-for-spec/evals/evals.json` — two scenarios)
9. **Reported bug filed as a tracked fix** (`skills/issue-tracker/evals/evals.json`)
10. **Module-level planning is inserted between decompose and implement**, the **solution-architect only plans (temporary design.md, no code)**, and **the planning step is skipped for a single-slice main-issue** (`agents/solution-architect/evals/evals.json` — three scenarios)
11. **Review Axis E checks the diff against design.md via design-reviewer when a plan exists**, and **falls back to clean-room when there is no plan** (`agents/design-reviewer/evals/evals.json` — two scenarios)

Read these files using the `view_file` tool to extract the `prompt` and `expectations` for each test case. Some files hold more than one scenario — run every case in the file, not just the first.

### 2. Execution
For each test case found, use the `invoke_subagent` tool to spawn an executor subagent.
* **Role:** `executor`
* **Workspace Mode:** `branch` (CRITICAL: Must be `branch` so it runs in an isolated worktree and cannot affect the main checkout).
* **Prompt:** "Execute the following scenario and return a detailed transcript of everything you did, including tool calls and outputs:\n\n<INSERT_SCENARIO_PROMPT_HERE>"

**Note:** Spawn all executor subagents in parallel in a single tool call to save time.

### 3. Grading
Once the executor subagents return their transcripts, evaluate each one against its expectations.
For each result, spawn a new grader subagent (or grade them inline if you are confident).
If spawning grader subagents:
* **Role:** `grader`
* **Prompt:** First, read your instructions in `skills/self-test/agents/grader.md`. Then grade the following transcript against these expectations:\n\nExpectations:\n<INSERT_EXPECTATIONS_HERE>\n\nTranscript:\n<INSERT_TRANSCRIPT_HERE>\n\nReturn the grading object in the JSON schema defined in your instructions.

### 4. Reporting
Once all grading is complete, present a Markdown table to the user summarizing the results. The table should have columns for:
* **Test** (the `name` from the `evals.json`)
* **Expected** (usually "pass")
* **Result** ("✓ pass" or "✗ FAIL")
* **Details** (If failed, brief reason from the grader)

If any test fails, inform the user clearly.
