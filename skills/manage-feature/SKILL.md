---
name: manage-feature
description: Central skill for all CRUD operations on features. Provides a deterministic Python script to manage the `docs/features/` workspace.
user-invocable: false
---

# Manage Feature

Use this skill as a utility to interact with the feature workspace (the `docs/features/` directory). 
This skill provides a robust, deterministic Python script `scripts/feature.py` to handle all file operations instead of relying on manual markdown parsing.

## Usage

The script `feature.py` is located in the `scripts/` directory of this skill. Since the skill may be installed globally (e.g., in `~/.gemini/config/skills/`) or locally in the project, you must dynamically locate its path before execution.

You can execute the script using `python3 <path-to-manage-feature-skill>/scripts/feature.py <command>`.

### Available Commands:

1. **`init <slug> <title>`**
   - Creates the directories `docs/features/<slug>/` and `docs/features/<slug>/issues/`.
   - Creates a template `PRD.md` for the feature.
   - Sets the feature as active (`docs/features/active-feature.txt`).

2. **`get-active`**
   - Reads `docs/features/active-feature.txt` and prints the active feature slug.
   - Exits with an error if no active feature is set.

3. **`set-active <slug>`**
   - Sets the given slug as the active feature.

4. **`next-issue`**
   - Scans `docs/features/<active-feature-slug>/issues/` for the next unblocked issue.
   - An issue is unblocked if its status is `Status: ready-for-agent` AND all issues listed in `Blocked by:` have `Status: resolved`.
   - Prints the file path of the next issue. Exits with an error if none are found.

5. **`update-issue <issue-file-path> <new-status>`**
   - Updates the status of the specified issue markdown file to the `<new-status>` (e.g., `claimed`, `resolved`).

6. **`complete`**
   - Deletes `docs/features/active-feature.txt` when a feature is fully resolved.

7. **`list-open-features`**
   - Prints a list of all features in `docs/features/` that have at least one unresolved issue.
