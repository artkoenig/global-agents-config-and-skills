---
name: implement-with-ticket
description: Sequentially implements the open issues tracked by the local issue-tracker (markdown issues under `docs/issues/`), delegating the actual coding to the code-generation-principles. It picks the next ready issue, claims it, implements only what that issue specifies, verifies against its acceptance criteria, and resolves it. Use only when this local issue tracker is present; for ad-hoc code changes without tracked issues, do not use this skill.
user-invocable: true
---

# Implementation (Issue-Based)

Use this skill to systematically work through the open issues of a project's
local issue tracker. Process issues one at a time; for each, repeat steps 1–4.

The tracker is owned by the `issue-tracker` skill — all issue state changes go
through its `tracker.py` script so the state machine and blocker rules hold.
Resolve `<skill>` below to the path of the `issue-tracker` skill's script.

## Workflow

### 1. Find the next actionable issue
- Ask the tracker for the next unblocked, `ready-for-agent` **leaf** issue:
  ```bash
  ID=$(python3 <skill>/scripts/tracker.py next)
  ```
  Scope to a subtree with `next --parent <id>` when the user wants to focus on
  one feature. If nothing is returned, there is no ready work — stop and report.
- Claim it:
  ```bash
  python3 <skill>/scripts/tracker.py set-status "$ID" claimed
  ```
- Show the issue and its acceptance criteria to the user:
  ```bash
  python3 <skill>/scripts/tracker.py show "$ID"
  ```
- Implement **only** what this issue specifies. Do not anticipate work from other
  issues.

### 2. Implement the issue
- If not already done, create or check out a branch for the work (e.g.
  `issue/<slug>`).
- Implement in small, incremental units, following the `code-generation-principles`
  skill (meaningful names, SRP, comprehensive unit tests, etc.).
- Run the project's test suite and verify that all tests pass and the issue's
  acceptance criteria are met.

### 3. Resolve the issue
- Once implemented and green, follow the `issue-tracker` skill's resolve workflow:
  append a short solution summary as a comment and set the status to `resolved`.
  ```bash
  python3 <skill>/scripts/tracker.py comment "$ID" "<short solution summary>"
  python3 <skill>/scripts/tracker.py set-status "$ID" resolved
  ```

### 4. Continue or hand off
- Repeat from step 1 for the next issue. When no ready issues remain, give the
  user a brief summary of the changes made and the state of the git repository.
