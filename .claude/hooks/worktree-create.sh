#!/usr/bin/env bash
# Claude Code WorktreeCreate hook: redirect Claude Code's native worktree paths
# (EnterWorktree, --worktree, isolation: "worktree", background sessions) into
# this repo's .worktrees/<name> convention instead of the default
# .claude/worktrees/, per AGENTS.md's "Worktree Isolation" rule.
#
# Without this hook a native worktree lands in .claude/worktrees/, sidestepping
# the .worktrees/ convention and its .gitignore entry. The hook replaces the
# default git behavior: it creates the worktree under .worktrees/ itself and
# prints the resulting path, which is the contract Claude Code expects.
#
# Installed as a project's .claude/hooks/worktree-create.sh, wired into
# .claude/settings.json's hooks.WorktreeCreate, by the cloud-session-bootstrap
# skill. Kept byte-identical to this asset (a deterministic self-test binds the
# two), so there is a single source of truth for the redirect logic rather than
# a bash blob duplicated inline in every settings.json.
#
# WorktreeCreate JSON contract (see https://code.claude.com/docs/en/hooks.md):
#   stdin:  {"worktree_name": ..., "base_ref": ...}
#   stdout: the absolute path of the created worktree directory (nothing else).
#           A non-zero exit or missing path fails worktree creation.
set -euo pipefail

input=$(cat)
name=$(jq -r .worktree_name <<<"$input")
base=$(jq -r .base_ref <<<"$input")
root=$(git rev-parse --show-toplevel)
dir="$root/.worktrees/$name"

# git's own stdout goes to stderr so the created path is the only thing on our
# stdout, as the hook contract requires.
git worktree add "$dir" "$base" >&2
echo "$dir"
