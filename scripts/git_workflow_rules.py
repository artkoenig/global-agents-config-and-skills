#!/usr/bin/env python3
"""Deterministic git workflow rule checks.

This module has two roles that stay strictly separated:

  1. Pure, importable predicates with no git and no I/O — the part that is
     unit-tested directly:
       - is_protected_ref(ref)
       - commit_has_agent_coauthor(message)
       - is_trivial_change(files, added_lines)

  2. A thin CLI that gathers git state and applies those predicates. It backs
     both the `.githooks/pre-push` hook and manual invocation, so the exact
     same logic runs at push time and on demand.

Rules enforced (PRD user stories 8-9):
  8. A push whose target ref is a protected branch (main/master) is rejected;
     protected branches move only through a GitHub PR merge.
  9. A pushed commit whose message carries a Co-authored-by trailer is rejected
     (single-maintainer repo, no allow-list).

Branch names are intentionally NOT enforced (PRD user story 7 was dropped): a
cloud (Claude Code on the web) session runs on a platform-assigned branch such
as ``claude/<slug>`` that the session cannot rename, so a ``^issue/`` gate would
reject every remote push. ``issue/<slug>`` stays the recommended convention.

is_trivial_change is not a push gate — triviality governs whether a change may
skip issue tracking, a decision the hook cannot observe. It lives here because
it is deterministic, belongs to the same rule set, and is unit-tested.

Exit status of the CLI: 0 = all checks pass, 1 = at least one violation,
2 = usage error. At push time, `git push --no-verify` is the sanctioned bypass.

Usage:
  git_workflow_rules.py pre-push [<remote> <url>]   # reads push lines on stdin
  git_workflow_rules.py check                       # checks the current checkout
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import PurePosixPath

PROTECTED_REFS = frozenset({"main", "master"})
TRIVIAL_EXTENSIONS = frozenset({".md", ".json", ".yaml", ".yml", ".txt"})
# A Co-authored-by trailer: a line that starts (ignoring leading blanks) with
# the token and carries a non-blank value. Prose mentioning the phrase mid-line
# does not match. Git treats the trailer token case-insensitively, so do we.
COAUTHOR_RE = re.compile(r"^[ \t]*co-authored-by:[ \t]*\S", re.IGNORECASE | re.MULTILINE)
_HEADS_PREFIX = "refs/heads/"


# --------------------------------------------------------------------------- #
# Pure predicates (no git, no I/O)                                            #
# --------------------------------------------------------------------------- #

def is_protected_ref(ref: str) -> bool:
    """True if ``ref`` names a protected branch that must never receive a push.

    Accepts either the bare name (``main``) or the fully-qualified form
    (``refs/heads/main``).
    """
    return _strip_heads(ref) in PROTECTED_REFS


def commit_has_agent_coauthor(message: str) -> bool:
    """True if the commit message carries any Co-authored-by trailer.

    No allow-list: in a single-maintainer repo any co-author is a violation.
    """
    return COAUTHOR_RE.search(message) is not None


def is_trivial_change(files, added_lines: int) -> bool:
    """True if a change is trivial enough to skip issue tracking.

    Trivial means exactly one changed file AND either at most one added line or
    that file carrying a docs/config extension.
    """
    files = list(files)
    if len(files) != 1:
        return False
    if added_lines <= 1:
        return True
    return PurePosixPath(files[0]).suffix.lower() in TRIVIAL_EXTENSIONS


# --------------------------------------------------------------------------- #
# Small internal helpers with their own logic (unit-tested)                   #
# --------------------------------------------------------------------------- #

def _strip_heads(ref: str) -> str:
    """Drop a leading ``refs/heads/`` prefix, leaving the branch name intact.

    Only that prefix is removed, so slashes inside a branch name (``issue/x``)
    survive.
    """
    return ref[len(_HEADS_PREFIX):] if ref.startswith(_HEADS_PREFIX) else ref


def _is_zero_sha(sha: str) -> bool:
    """True for git's all-zero sentinel sha (a created or deleted ref)."""
    return len(sha) > 0 and set(sha) == {"0"}


# --------------------------------------------------------------------------- #
# Git plumbing                                                                #
# --------------------------------------------------------------------------- #

def _run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def _commits_in_range(local_sha: str, remote_sha: str) -> list[str]:
    """The commit shas this push introduces, excluding what the remote has."""
    if _is_zero_sha(remote_sha):
        # New branch on the remote: everything not already on some remote ref.
        args = ["rev-list", local_sha, "--not", "--remotes"]
    else:
        args = ["rev-list", f"{remote_sha}..{local_sha}"]
    out = _run_git(*args).strip()
    return out.splitlines() if out else []


def _commit_message(sha: str) -> str:
    return _run_git("show", "-s", "--format=%B", sha)


def _current_branch() -> str | None:
    try:
        return _run_git("symbolic-ref", "--short", "HEAD").strip()
    except subprocess.CalledProcessError:
        return None  # detached HEAD


def _local_commits() -> list[str]:
    """Commits on HEAD not yet on any remote-tracking ref."""
    out = _run_git("rev-list", "HEAD", "--not", "--remotes").strip()
    return out.splitlines() if out else []


# --------------------------------------------------------------------------- #
# Checks that turn git state into violation messages                          #
# --------------------------------------------------------------------------- #

def _check_push_line(
    _local_ref: str, local_sha: str, remote_ref: str, remote_sha: str
) -> list[str]:
    violations: list[str] = []

    if _is_zero_sha(local_sha):
        return violations  # deleting a remote ref: nothing to validate

    # Rule 8: the target ref must not be a protected branch.
    if is_protected_ref(remote_ref):
        violations.append(
            f"push target '{_strip_heads(remote_ref)}' is protected; "
            "update it through a GitHub PR merge, not a local push"
        )

    # Rule 9: no pushed commit may carry a Co-authored-by trailer.
    for sha in _commits_in_range(local_sha, remote_sha):
        if commit_has_agent_coauthor(_commit_message(sha)):
            violations.append(
                f"commit {sha[:12]} carries a Co-authored-by trailer "
                "(not allowed in this repo)"
            )
    return violations


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #

def _report(violations: list[str]) -> int:
    if not violations:
        return 0
    print("Git workflow check failed:", file=sys.stderr)
    for v in violations:
        print(f"  - {v}", file=sys.stderr)
    print(
        "\nBypass with `git push --no-verify` if this is deliberate.",
        file=sys.stderr,
    )
    return 1


def _cmd_pre_push(_argv: list[str]) -> int:
    violations: list[str] = []
    for line in sys.stdin:
        parts = line.split()
        if len(parts) != 4:
            continue
        try:
            violations.extend(_check_push_line(*parts))
        except subprocess.CalledProcessError as exc:
            # Fail closed with a clean message rather than a traceback.
            violations.append(f"could not inspect push ({parts}): {exc}")
    return _report(violations)


def _cmd_check(_argv: list[str]) -> int:
    branch = _current_branch()
    if branch is None:
        print("workflow-check: detached HEAD, nothing to check", file=sys.stderr)
        return 0

    violations: list[str] = []
    if is_protected_ref(branch):
        violations.append(f"currently on protected branch '{branch}'")
    try:
        for sha in _local_commits():
            if commit_has_agent_coauthor(_commit_message(sha)):
                violations.append(
                    f"commit {sha[:12]} carries a Co-authored-by trailer "
                    "(not allowed in this repo)"
                )
    except subprocess.CalledProcessError as exc:
        violations.append(f"could not inspect local commits: {exc}")
    return _report(violations)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv[0] if argv else "check"
    rest = argv[1:]
    if command == "pre-push":
        return _cmd_pre_push(rest)
    if command == "check":
        return _cmd_check(rest)
    print(f"unknown command: {command!r} (expected 'pre-push' or 'check')",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
