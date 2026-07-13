---
name: git-principles
description: MANDATORY FIRST STEP. This skill MUST be read and applied BEFORE exploring the codebase, searching, listing directories, or reading files. It contains mandatory git branch and status checks.
user-invocable: false
---

# Git & Version-Control Principles

Apply these rules whenever the files you are about to work on are versioned (tracked in a git repository).

## Before reading and analyzing project files

- Always check whether the files you are about to modify are versioned.
- Print the current branch name and ask the user whether to use it or create a new branch.
- Always check, if you are on the right branch for the planned changes and you fetched and pulled from origin
- **PR Follow-up Protection:** If changes are requested on a branch that already has an open or recently completed Pull Request (PR), explicitly ask the user if a new branch should be created for these additional changes instead of reusing the old branch.

## Commits & pushes

- Never commit or push changes automatically.
  Only commit or push when the user explicitly asks for it.
- When writing commit messages, never auto-add your agent name as co-author.
- Keep the repository clean: if orphaned or merged branches exist, ask the user if they should be deleted
