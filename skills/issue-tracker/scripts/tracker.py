#!/usr/bin/env python3
"""Deterministic engine for the local, file-based issue tracker.

Issues form a recursive tree under a root directory (default: ``docs/issues``).
Each issue is a directory ``NN-<slug>/`` holding an ``issue.md`` that describes
it; child issues live in subdirectories of their parent's directory. A
"feature" is therefore just an issue that happens to have children, and its
``issue.md`` is that feature's specification. This keeps the whole workspace to
a single concept — an *issue* — at arbitrary depth (epic -> feature -> task).

The script is intentionally deterministic so that skills never have to parse
markdown by hand. Run ``tracker.py selftest`` to exercise the engine.
"""

import argparse
import os
import re
import sys

DEFAULT_ROOT = os.path.join("docs", "issues")
ISSUE_FILE = "issue.md"
ROOT_ENV_VAR = "ISSUE_TRACKER_DIR"

# The five issue states and the transitions allowed between them. Making the
# state machine explicit prevents inconsistent lifecycles — e.g. jumping from
# needs-triage straight to resolved without the work in between.
STATES = ["needs-triage", "needs-info", "ready-for-agent", "claimed", "resolved"]
TRANSITIONS = {
    "needs-triage": {"needs-info", "ready-for-agent"},
    "needs-info": {"ready-for-agent", "needs-triage"},
    "ready-for-agent": {"claimed", "needs-info"},
    "claimed": {"resolved", "ready-for-agent"},
    "resolved": {"ready-for-agent"},  # reopen
}
DEFAULT_STATUS = "needs-triage"

ISSUE_TEMPLATE = """Status: {status}
Blocked by: {blocked_by}

## Description
{title}

## Acceptance Criteria
- [ ]

## Comments
"""

# Marker used to keep the AGENTS.md/CLAUDE.md wiring idempotent across re-runs.
AGENTS_MARKER = "### Issue tracker"
AGENTS_BLOCK = """## Agent skills

### Issue tracker
This project tracks work as local markdown issues under `docs/issues/`, managed
through the `issue-tracker` skill. Everything is an *issue*: a directory
`NN-<slug>/` with an `issue.md`; features are issues with child issues nested
inside them. Do not edit issue files by hand — use the `issue-tracker` skill so
status transitions stay valid.

When asked to change or add code, first judge the scope. Implement a small,
self-contained change directly. For anything larger, create an issue for it
first (`tracker.py create`), then implement it through the tracked workflow in
`docs/agents/issue-tracker.md` (which also documents the state model).
"""

TRACKER_DOC = """# Issue tracker: local markdown

Work for this repository is tracked as a recursive tree of markdown issues.

## Layout
- Root: `docs/issues/`
- Each issue is a directory `NN-<slug>/` containing an `issue.md`.
- Child issues are subdirectories of their parent. A "feature" is just an issue
  with children; its `issue.md` holds the specification (PRD).
- An issue is addressed by its path relative to `docs/issues/`,
  e.g. `01-checkout/02-cart-api`.

## States (enforced transitions)
- `needs-triage` — awaiting evaluation by the maintainer
- `needs-info` — waiting for feedback
- `ready-for-agent` — fully specified, ready for autonomous implementation (AFK)
- `claimed` — in progress by the agent
- `resolved` — implemented and done

Allowed transitions:
- `needs-triage` -> `needs-info`, `ready-for-agent`
- `needs-info` -> `ready-for-agent`, `needs-triage`
- `ready-for-agent` -> `claimed`, `needs-info`
- `claimed` -> `resolved`, `ready-for-agent`
- `resolved` -> `ready-for-agent` (reopen)

A parent issue cannot become `resolved` while any child is still open.

## Implementing an issue
Work issues one at a time. For each:
1. Pick the next actionable issue with `tracker.py next` (add `--parent <id>` to
   focus on one feature). It returns the next `ready-for-agent` leaf whose
   blockers are all `resolved`. If nothing is returned, there is no ready work.
2. Claim it: `tracker.py set-status <id> claimed`, and read it with
   `tracker.py show <id>`.
3. Implement **only** what that issue specifies — do not anticipate other issues.
   Work in small increments on a branch (e.g. `issue/<slug>`), following this
   project's engineering principles (meaningful names, single responsibility,
   comprehensive tests).
4. Run the test suite; verify all tests pass and the acceptance criteria are met.
5. Resolve it: append a short solution summary with
   `tracker.py comment <id> "..."`, then `tracker.py set-status <id> resolved`.

Repeat until `next` reports no ready issues.

## Do not hand-edit
Manage issues through the `issue-tracker` skill's `tracker.py` so that the state
machine and blocker rules are respected.
"""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def fail(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def get_root():
    return os.environ.get(ROOT_ENV_VAR, DEFAULT_ROOT)


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "issue"


def normalize_id(raw):
    """Turn user input into a canonical issue id (path relative to the root).

    Accepts a bare id (``01-foo/02-bar``), a path that still carries the root
    prefix, or a path pointing directly at an ``issue.md``.
    """
    raw = raw.strip().replace(os.sep, "/").strip("/")
    if raw.endswith("/" + ISSUE_FILE):
        raw = raw[: -(len(ISSUE_FILE) + 1)]
    root = get_root().replace(os.sep, "/").strip("/")
    if root and (raw == root or raw.startswith(root + "/")):
        raw = raw[len(root):].strip("/")
    return raw


def issue_dir(issue_id):
    parts = [p for p in issue_id.split("/") if p]
    return os.path.join(get_root(), *parts)


def issue_file(issue_id):
    return os.path.join(issue_dir(issue_id), ISSUE_FILE)


def exists(issue_id):
    return os.path.exists(issue_file(issue_id))


def read_field(issue_id, field):
    path = issue_file(issue_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        for line in f:
            if line.startswith(field + ":"):
                return line.split(":", 1)[1].strip()
    return None


def set_field(issue_id, field, value):
    path = issue_file(issue_id)
    with open(path) as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith(field + ":"):
            lines[i] = f"{field}: {value}\n"
            break
    else:
        lines.insert(0, f"{field}: {value}\n")
    with open(path, "w") as f:
        f.writelines(lines)


def get_status(issue_id):
    return read_field(issue_id, "Status")


def child_ids(issue_id):
    """Direct child issue ids of ``issue_id`` (or of the root when empty)."""
    parent = issue_dir(issue_id) if issue_id else get_root()
    if not os.path.isdir(parent):
        return []
    ids = []
    for name in sorted(os.listdir(parent)):
        if os.path.exists(os.path.join(parent, name, ISSUE_FILE)):
            ids.append(f"{issue_id}/{name}" if issue_id else name)
    return ids


def is_leaf(issue_id):
    return not child_ids(issue_id)


def walk(issue_id=""):
    """Depth-first pre-order traversal yielding every descendant issue id."""
    for cid in child_ids(issue_id):
        yield cid
        yield from walk(cid)


def parent_of(issue_id):
    return issue_id.rsplit("/", 1)[0] if "/" in issue_id else ""


def next_prefix(parent_id):
    parent = issue_dir(parent_id) if parent_id else get_root()
    max_n = 0
    if os.path.isdir(parent):
        for name in os.listdir(parent):
            match = re.match(r"(\d+)-", name)
            if match and os.path.exists(os.path.join(parent, name, ISSUE_FILE)):
                max_n = max(max_n, int(match.group(1)))
    return f"{max_n + 1:02d}"


def format_blocked(raw):
    if not raw:
        return "None"
    nums = [n.zfill(2) for n in re.findall(r"\d+", raw)]
    return "[" + ", ".join(nums) + "]" if nums else "None"


def get_blockers(issue_id):
    raw = read_field(issue_id, "Blocked by") or ""
    if raw.strip().lower() in ("", "none", "[]"):
        return []
    return re.findall(r"\d+", raw)


def sibling_by_number(issue_id, num):
    for sib in child_ids(parent_of(issue_id)):
        match = re.match(r"(\d+)-", sib.rsplit("/", 1)[-1])
        if match and int(match.group(1)) == int(num):
            return sib
    return None


def is_unblocked(issue_id):
    for num in get_blockers(issue_id):
        sib = sibling_by_number(issue_id, num)
        if not sib or get_status(sib) != "resolved":
            return False
    return True


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def cmd_create(args):
    parent_id = normalize_id(args.parent) if args.parent else ""
    if parent_id and not exists(parent_id):
        fail(f"Parent issue not found: {parent_id}")

    status = args.status or DEFAULT_STATUS
    if status not in STATES:
        fail(f"Unknown status '{status}'. Valid: {', '.join(STATES)}")

    name = f"{next_prefix(parent_id)}-{slugify(args.title)}"
    new_id = f"{parent_id}/{name}" if parent_id else name
    os.makedirs(issue_dir(new_id), exist_ok=True)
    with open(issue_file(new_id), "w") as f:
        f.write(ISSUE_TEMPLATE.format(
            status=status,
            blocked_by=format_blocked(args.blocked_by),
            title=args.title,
        ))
    print(new_id)


def cmd_list(args):
    start = normalize_id(args.parent) if args.parent else ""
    base_depth = start.count("/") + 1 if start else 0
    found = False
    for issue_id in walk(start):
        status = get_status(issue_id)
        if args.status and status != args.status:
            continue
        found = True
        if args.tree:
            indent = "  " * (issue_id.count("/") - base_depth)
            label = indent + issue_id.rsplit("/", 1)[-1]
        else:
            label = issue_id
        container = "" if is_leaf(issue_id) else "/"
        print(f"{label}{container}  [{status}]")
    if not found:
        print("(no matching issues)")


def cmd_show(args):
    issue_id = normalize_id(args.issue)
    if not exists(issue_id):
        fail(f"Issue not found: {issue_id}")
    with open(issue_file(issue_id)) as f:
        sys.stdout.write(f.read())


def cmd_set_status(args):
    issue_id = normalize_id(args.issue)
    if not exists(issue_id):
        fail(f"Issue not found: {issue_id}")

    new = args.status
    if new not in STATES:
        fail(f"Unknown status '{new}'. Valid: {', '.join(STATES)}")

    current = get_status(issue_id)
    if new != current and new not in TRANSITIONS.get(current, set()):
        allowed = ", ".join(sorted(TRANSITIONS.get(current, set()))) or "none"
        fail(f"Invalid transition {current} -> {new}. Allowed from {current}: {allowed}")

    if new == "resolved":
        open_children = [c for c in child_ids(issue_id) if get_status(c) != "resolved"]
        if open_children:
            fail(f"Cannot resolve '{issue_id}' while child issues are open: "
                 f"{', '.join(open_children)}")

    set_field(issue_id, "Status", new)
    print(f"{issue_id}: {current} -> {new}")


def cmd_comment(args):
    issue_id = normalize_id(args.issue)
    if not exists(issue_id):
        fail(f"Issue not found: {issue_id}")
    with open(issue_file(issue_id)) as f:
        content = f.read()
    if "## Comments" not in content:
        content = content.rstrip() + "\n\n## Comments\n"
    content = content.rstrip() + f"\n- {args.text}\n"
    with open(issue_file(issue_id), "w") as f:
        f.write(content)
    print(f"Comment added to {issue_id}")


def cmd_next(args):
    start = normalize_id(args.parent) if args.parent else ""
    for issue_id in walk(start):
        if is_leaf(issue_id) and get_status(issue_id) == "ready-for-agent" \
                and is_unblocked(issue_id):
            print(issue_id)
            return
    fail("No unblocked ready-for-agent leaf issue found.")


# --------------------------------------------------------------------------- #
# init: scaffold structure and wire the tracker into AGENTS.md / CLAUDE.md
# --------------------------------------------------------------------------- #

def _write_if_absent(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(content)
        return True
    return False


def _ensure_gitignore_scratch():
    path = ".gitignore"
    entry = ".scratch/"
    existing = ""
    if os.path.exists(path):
        with open(path) as f:
            existing = f.read()
    if entry not in existing.split():
        with open(path, "a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(entry + "\n")


def _pick_agents_file(explicit):
    if explicit:
        return explicit
    for candidate in ("AGENTS.md", "CLAUDE.md"):
        if os.path.exists(candidate):
            return candidate
    return "AGENTS.md"


def _wire_agents_file(target):
    existing = ""
    if os.path.exists(target):
        with open(target) as f:
            existing = f.read()
    if AGENTS_MARKER in existing:
        return False  # already wired — keep idempotent
    with open(target, "w") as f:
        if existing.strip():
            f.write(existing.rstrip() + "\n\n" + AGENTS_BLOCK)
        else:
            f.write(AGENTS_BLOCK)
    return True


def cmd_init(args):
    root = get_root()
    os.makedirs(root, exist_ok=True)
    _write_if_absent(os.path.join(root, ".gitkeep"), "")
    _write_if_absent(os.path.join("docs", "agents", "issue-tracker.md"), TRACKER_DOC)
    _ensure_gitignore_scratch()
    target = _pick_agents_file(args.agents_file)
    wired = _wire_agents_file(target)
    note = "added" if wired else "already present"
    print(f"Issue tracker initialized at {root}/. Agent note in {target} ({note}).")


# --------------------------------------------------------------------------- #
# selftest
# --------------------------------------------------------------------------- #

def cmd_selftest(_args):
    import tempfile
    from types import SimpleNamespace

    with tempfile.TemporaryDirectory() as tmp:
        os.environ[ROOT_ENV_VAR] = os.path.join(tmp, "docs", "issues")

        def create(title, parent=None, status=None, blocked_by=None):
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd_create(SimpleNamespace(title=title, parent=parent,
                                           status=status, blocked_by=blocked_by))
            return buf.getvalue().strip()

        feature = create("Checkout redesign", status="ready-for-agent")
        assert feature == "01-checkout-redesign", feature
        a = create("Cart schema", parent=feature, status="ready-for-agent")
        b = create("Cart API", parent=feature, status="ready-for-agent", blocked_by="1")
        bug = create("Login bug")  # default needs-triage, top-level leaf
        assert bug == "02-login-bug", bug
        assert get_status(bug) == "needs-triage"

        # next: first ready-for-agent leaf, and 'b' is blocked by 'a'.
        assert not is_leaf(feature) and is_leaf(a) and is_leaf(b)
        assert is_unblocked(a) and not is_unblocked(b)

        # Enforced transitions: needs-triage -> resolved is illegal.
        try:
            cmd_set_status(SimpleNamespace(issue=bug, status="resolved"))
            raise AssertionError("illegal transition was allowed")
        except SystemExit:
            pass

        # Parent cannot resolve while children are open.
        cmd_set_status(SimpleNamespace(issue=a, status="claimed"))
        cmd_set_status(SimpleNamespace(issue=a, status="resolved"))
        assert is_unblocked(b)  # blocker a now resolved
        try:
            cmd_set_status(SimpleNamespace(issue=feature, status="claimed"))
            # feature is ready-for-agent -> claimed is valid; but resolve must fail:
            cmd_set_status(SimpleNamespace(issue=feature, status="resolved"))
            raise AssertionError("resolved parent with open child")
        except SystemExit:
            pass

        # Resolve child b, then parent can resolve.
        cmd_set_status(SimpleNamespace(issue=b, status="claimed"))
        cmd_set_status(SimpleNamespace(issue=b, status="resolved"))
        cmd_set_status(SimpleNamespace(issue=feature, status="resolved"))
        assert get_status(feature) == "resolved"

    del os.environ[ROOT_ENV_VAR]
    print("selftest: OK")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser():
    parser = argparse.ArgumentParser(description="Local file-based issue tracker.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Scaffold docs/issues and wire AGENTS.md/CLAUDE.md.")
    p_init.add_argument("--agents-file", help="Force AGENTS.md or CLAUDE.md target.")
    p_init.set_defaults(func=cmd_init)

    p_create = sub.add_parser("create", help="Create a new issue.")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--parent", help="Parent issue id to nest under.")
    p_create.add_argument("--status", help=f"Initial status (default {DEFAULT_STATUS}).")
    p_create.add_argument("--blocked-by", help="Comma-separated sibling numbers.")
    p_create.set_defaults(func=cmd_create)

    p_list = sub.add_parser("list", help="List issues.")
    p_list.add_argument("--parent", help="Restrict to a subtree.")
    p_list.add_argument("--status", help="Filter by status.")
    p_list.add_argument("--tree", action="store_true", help="Indented tree view.")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Print an issue's markdown.")
    p_show.add_argument("issue")
    p_show.set_defaults(func=cmd_show)

    p_status = sub.add_parser("set-status", help="Change status (enforced transitions).")
    p_status.add_argument("issue")
    p_status.add_argument("status")
    p_status.set_defaults(func=cmd_set_status)

    p_comment = sub.add_parser("comment", help="Append a comment.")
    p_comment.add_argument("issue")
    p_comment.add_argument("text")
    p_comment.set_defaults(func=cmd_comment)

    p_next = sub.add_parser("next", help="Print the next actionable leaf issue.")
    p_next.add_argument("--parent", help="Restrict to a subtree.")
    p_next.set_defaults(func=cmd_next)

    sub.add_parser("selftest", help="Run the built-in engine tests.").set_defaults(func=cmd_selftest)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
