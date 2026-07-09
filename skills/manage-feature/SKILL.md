---
name: manage-feature
description: Central skill for all CRUD operations on features. Provides a deterministic Python script to manage the `.scratch/` workspace.
user-invocable: false
---

# Manage Feature

Use this skill as a utility to interact with the feature workspace (the `.scratch/` directory). 
This skill provides a robust, deterministic Python script `scripts/feature.py` to handle all file operations instead of relying on manual markdown parsing.

## Usage

You can execute the script from the project root using `python3 .agents/skills/manage-feature/scripts/feature.py <command>`.

### Available Commands:

1. **`init <slug> <title>`**
   - Creates the directories `.scratch/<slug>/` and `.scratch/<slug>/issues/`.
   - Creates a template `PRD.md` for the feature.
   - Sets the feature as active (`.scratch/active-feature.txt`).

2. **`get-active`**
   - Reads `.scratch/active-feature.txt` and prints the active feature slug.
   - Exits with an error if no active feature is set.

3. **`set-active <slug>`**
   - Sets the given slug as the active feature.

4. **`next-issue`**
   - Scans `.scratch/<active-feature-slug>/issues/` for the next unblocked issue.
   - An issue is unblocked if its status is `Status: ready-for-agent` AND all issues listed in `Blocked by:` have `Status: resolved`.
   - Prints the file path of the next issue. Exits with an error if none are found.

5. **`update-issue <issue-file-path> <new-status>`**
   - Updates the status of the specified issue markdown file to the `<new-status>` (e.g., `claimed`, `resolved`).

6. **`complete`**
   - Deletes `.scratch/active-feature.txt` when a feature is fully resolved.

7. **`list-open-features`**
   - Prints a list of all features in `.scratch/` that have at least one unresolved issue.
