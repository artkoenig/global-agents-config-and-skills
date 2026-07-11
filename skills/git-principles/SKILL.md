---
name: git-principles
description: Git and version-control workflow rules that apply whenever the files being worked on are versioned (tracked in a git repository). Use before making any change to versioned files, and when committing, branching, or pushing: verify the files are versioned, print the current branch and ask whether to use it or create a new branch, never commit or push automatically, and never add the agent as commit co-author.
user-invocable: false
---

# Git & Version-Control Principles

Apply these rules whenever the files you are about to work on are versioned (tracked in a git repository).

## Before making changes

- Always check whether the files you are about to modify are versioned.
- Print the current branch name and ask the user whether to use it or create a new branch.

## Commits & pushes

- Never commit or push changes automatically.
  Only commit or push when the user explicitly asks for it.
- When writing commit messages, never auto-add your agent name as co-author.
