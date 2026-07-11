# Workflow: Implement tracked issues

Use this workflow to work through the open issues of a project one at a time.
Each issue's lifecycle runs `ready-for-agent → claimed → resolved`; the tracker
enforces the transitions, so all state changes go through `tracker.py`.

Resolve `<skill>` below to the path of the `issue-tracker` skill's script.

## Loop — repeat for each issue

### 1. Find the next actionable issue
```bash
ID=$(python3 <skill>/scripts/tracker.py next)
```
`next` returns the next unblocked `ready-for-agent` **leaf** issue. Add
`--parent <id>` to focus on a single feature. If nothing is returned, there is no
ready work — stop and report.

Claim it and read it:
```bash
python3 <skill>/scripts/tracker.py set-status "$ID" claimed
python3 <skill>/scripts/tracker.py show "$ID"
```

### 2. Implement
Implement **only** what this issue specifies — do not anticipate other issues.
Work in small increments on a branch (e.g. `issue/<slug>`). For the coding
itself, follow the `code-generation-principles` skill (meaningful names, single
responsibility, comprehensive tests). Then run the project's test suite and
verify all tests pass and the issue's acceptance criteria are met.

### 3. Resolve
Follow [resolve.md](resolve.md): append a short solution summary as a comment and
set the status to `resolved`.

### 4. Continue or hand off
Repeat from step 1. When no ready issues remain, give the user a brief summary of
the changes made and the state of the git repository.

## Note

This workflow is also written into a project by `tracker.py init` (into
`docs/agents/issue-tracker.md`), so an agent working in an initialized project
knows how to implement tracked work without invoking this skill explicitly.
