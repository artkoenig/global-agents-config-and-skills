#!/usr/bin/env python3
"""Deterministic engine for the local, file-based issue tracker.

Work is organised in two levels under a root directory (default:
``docs/issues``). A top-level directory ``NN-<slug>/`` is a **main-issue**: it
maps 1:1 to one branch ``issue/<slug>``, one worktree and one pull request, and
its ``issue.md`` holds the specification (PRD). The subdirectories nested inside
it are its **child-issues** — the vertically-sliced, independently implementable
units of that one PR. Every issue is the same thing on disk (a directory
``NN-<slug>/`` with an ``issue.md``), so the engine treats them uniformly and a
child-issue may itself be grouped a level deeper when a spec truly needs it; the
standard shape, and the one the workflows assume, is main-issue -> child-issues.

A main-issue additionally carries a ``Type:`` (feature|fix|refactor|chore) — the
change category that used to live in the old branch-name prefix. A child-issue
inherits its main-issue's type.

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

# The six issue states and the transitions allowed between them. Making the
# state machine explicit prevents inconsistent lifecycles — e.g. jumping from
# needs-triage straight to resolved without the work in between.
STATES = [
    "needs-triage",
    "needs-info",
    "ready-for-agent",
    "claimed",
    "resolved",
    "superseded",
]
TRANSITIONS = {
    "needs-triage": {"needs-info", "ready-for-agent", "superseded"},
    "needs-info": {"ready-for-agent", "needs-triage", "superseded"},
    "ready-for-agent": {"claimed", "needs-info", "superseded"},
    "claimed": {"resolved", "ready-for-agent", "superseded"},
    "resolved": {"ready-for-agent"},  # reopen; never superseded — done stays done
    "superseded": {"needs-triage"},  # reopen
}
DEFAULT_STATUS = "needs-triage"

# The states in which an issue is closed: no further work will happen on it.
# This is the single definition of "closed" — a closed blocker releases what it
# blocks, and a closed child-issue no longer holds up its main-issue. A future
# terminal state joins this set instead of spawning new string comparisons.
CLOSED_STATES = frozenset({"resolved", "superseded"})

# States whose transition demands a written justification, recorded as a comment
# on the issue. Without it an issue would drop off the board silently.
REASON_REQUIRED_STATES = frozenset({"superseded"})

# The change category a main-issue carries in its ``Type:`` field. It replaces
# the old branch-name prefix (feature|fix|refactor|chore) now that the only
# branch pattern is ``issue/<slug>``. Child-issues inherit their main-issue's
# type unless they override it.
TYPES = ["feature", "fix", "refactor", "chore"]

ISSUE_TEMPLATE = """Status: {status}
Type: {type}
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
through the `issue-tracker` skill. A top-level `NN-<slug>/` directory is a
**main-issue** — one branch `issue/<slug>`, one worktree, one pull request — and
its `issue.md` holds the spec; the directories nested inside it are its
**child-issues**, the vertical slices of that one PR. Do not edit issue files by
hand — use the `issue-tracker` skill so status transitions and blocker rules
stay valid.

See `docs/agents/issue-tracker.md` for the state model and the workflow for
implementing tracked issues.
"""

TRACKER_DOC = """# Issue tracker: local markdown

Work for this repository is tracked as local markdown issues in two levels.

## Layout
- Root: `docs/issues/`.
- A top-level `NN-<slug>/` directory is a **main-issue**: it maps 1:1 to one
  branch `issue/<slug>`, one worktree and one pull request, and its `issue.md`
  holds the specification (PRD). It carries a `Type:`
  (feature|fix|refactor|chore) — the change category that used to be a
  branch-name prefix.
- The directories nested inside a main-issue are its **child-issues** — the
  vertically-sliced units that make up that one PR. A child-issue inherits its
  main-issue's type.
- Each issue is a directory `NN-<slug>/` with an `issue.md`, addressed by its
  path relative to `docs/issues/`, e.g. `01-checkout/02-cart-api`.

## States (enforced transitions)
- `needs-triage` — awaiting evaluation by the maintainer
- `needs-info` — waiting for feedback
- `ready-for-agent` — fully specified, ready for autonomous implementation (AFK)
- `claimed` — in progress by the agent
- `resolved` — implemented and done
- `superseded` — closed without being implemented: replaced by another issue,
  made obsolete, or a duplicate. Which of those it was is stated in the
  mandatory reason, not in the state name.

Allowed transitions:
- `needs-triage` -> `needs-info`, `ready-for-agent`, `superseded`
- `needs-info` -> `ready-for-agent`, `needs-triage`, `superseded`
- `ready-for-agent` -> `claimed`, `needs-info`, `superseded`
- `claimed` -> `resolved`, `ready-for-agent`, `superseded`
- `resolved` -> `ready-for-agent` (reopen)
- `superseded` -> `needs-triage` (reopen)

`superseded` is reachable from every open state — work in progress can become
obsolete too — but never from `resolved`: finished work is not undone after the
fact. The transition requires a reason and is rejected without one:

```bash
tracker.py set-status <id> superseded --reason "Subsumed by 03-cart-rewrite."
```

The reason is recorded as a comment on the issue.

`resolved` and `superseded` both count as **closed**. A main-issue cannot become
`resolved` while any child-issue is still open, so it is "done" — and its PR
ready to open — only once its whole subtree is closed; a `superseded`
child-issue does not hold it up. Likewise a `superseded` blocker releases the
issues it blocks — otherwise an issue that will never be implemented would block
its neighbours forever.

## Implementing a main-issue
Every child-issue is implemented on the main-issue's one branch `issue/<slug>`;
the pull request is opened only once every child-issue is closed (`resolved`, or
`superseded` for a slice that turned out not to be needed).

Work the child-issues one at a time. For each:
1. Pick the next actionable child with `tracker.py next --parent <main-id>`. It
   returns the next `ready-for-agent` child whose blockers are all closed.
   If nothing is returned, there is no ready work.
2. Claim it: `tracker.py set-status <id> claimed`, and read it with
   `tracker.py show <id>`.
3. Implement **only** what that child specifies — do not anticipate other
   children. Follow this project's engineering principles (meaningful names,
   single responsibility, comprehensive tests).
4. Run the test suite; verify all tests pass and the acceptance criteria are met.
5. Resolve it: append a short solution summary with
   `tracker.py comment <id> "..."`, then `tracker.py set-status <id> resolved`.

Repeat until `next` reports no ready child. Then resolve the main-issue and open
the PR.

## Implementing several child-issues at once
`tracker.py next --parent <main-id> --all` prints every actionable child-issue
instead of just the first. Blocked issues are excluded, so the printed set is
independent by construction and safe to implement in parallel — one agent per
child, each in its own git worktree, none of them claiming through the
dispatcher (a worktree branches from the main-issue branch and never sees the
dispatcher's uncommitted claim).

Merge the finished child branches back into the main-issue branch **sequentially
in dependency order**. Numeric prefix order is a valid dependency order: a child
can only be blocked by a sibling that already existed when it was created, so
every blocker has a lower prefix. Remove each child worktree after its merge
(`git worktree remove`); no child branch outlives its merge.

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


def type_of(issue_id):
    return read_field(issue_id, "Type")


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


def is_closed(status):
    """Whether a status means the issue will see no further work.

    Both `resolved` (implemented) and `superseded` (never will be) close an
    issue. Everything that asks "is this issue still open?" asks it here.
    """
    return status in CLOSED_STATES


def is_unblocked(issue_id):
    for num in get_blockers(issue_id):
        sib = sibling_by_number(issue_id, num)
        if not sib or not is_closed(get_status(sib)):
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

    # A main-issue (no parent) must declare a type — it maps 1:1 to a branch and
    # the type replaces the old branch-name prefix. A child-issue inherits its
    # main-issue's type unless it overrides it, so every issue carries one.
    issue_type = args.type
    if issue_type and issue_type not in TYPES:
        fail(f"Unknown type '{issue_type}'. Valid: {', '.join(TYPES)}")
    if parent_id:
        issue_type = issue_type or type_of(parent_id)
    elif not issue_type:
        fail(f"--type is required for a main-issue. Valid: {', '.join(TYPES)}")

    name = f"{next_prefix(parent_id)}-{slugify(args.title)}"
    new_id = f"{parent_id}/{name}" if parent_id else name
    os.makedirs(issue_dir(new_id), exist_ok=True)
    with open(issue_file(new_id), "w") as f:
        f.write(ISSUE_TEMPLATE.format(
            status=status,
            type=issue_type,
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
        issue_type = type_of(issue_id)
        type_str = f"  ({issue_type})" if issue_type else ""
        print(f"{label}{container}  [{status}]{type_str}")
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

    reason = (getattr(args, "reason", None) or "").strip()
    if new in REASON_REQUIRED_STATES and not reason:
        fail(f"A transition to '{new}' requires a reason. Pass it with "
             f'--reason "why this issue is closed without being implemented"; '
             f"it is recorded as a comment on the issue.")

    if new == "resolved":
        open_children = [c for c in child_ids(issue_id)
                         if not is_closed(get_status(c))]
        if open_children:
            fail(f"Cannot resolve '{issue_id}' while child issues are open: "
                 f"{', '.join(open_children)}")

    set_field(issue_id, "Status", new)
    if reason:
        append_comment(issue_id, f"{new}: {reason}")
    print(f"{issue_id}: {current} -> {new}")


def append_comment(issue_id, text):
    """Append one bullet under the issue's `## Comments`, creating it if absent."""
    with open(issue_file(issue_id)) as f:
        content = f.read()
    if "## Comments" not in content:
        content = content.rstrip() + "\n\n## Comments\n"
    content = content.rstrip() + f"\n- {text}\n"
    with open(issue_file(issue_id), "w") as f:
        f.write(content)


def cmd_comment(args):
    issue_id = normalize_id(args.issue)
    if not exists(issue_id):
        fail(f"Issue not found: {issue_id}")
    append_comment(issue_id, args.text)
    print(f"Comment added to {issue_id}")


def find_actionable(start, limit=None):
    """Return the `ready-for-agent` child-issues (leaves) whose blockers are closed.

    Every issue in the result is independent of every other one: an issue that a
    sibling still blocks is excluded by `is_unblocked`. The full result is
    therefore the parallel-safe frontier — the set that may be worked on at the
    same time without one agent invalidating another's premise.
    """
    actionable = []
    for issue_id in walk(start):
        if is_leaf(issue_id) and get_status(issue_id) == "ready-for-agent" \
                and is_unblocked(issue_id):
            actionable.append(issue_id)
            if limit is not None and len(actionable) >= limit:
                break
    return actionable


def cmd_next(args):
    start = normalize_id(args.parent) if args.parent else ""
    actionable = find_actionable(start, limit=None if args.all else 1)
    if not actionable:
        fail("No unblocked ready-for-agent child-issue found.")
    for issue_id in actionable:
        print(issue_id)


# --------------------------------------------------------------------------- #
# init: scaffold structure and wire the tracker into AGENTS.md / CLAUDE.md
# --------------------------------------------------------------------------- #

TRACKER_DOC_PATH = os.path.join("docs", "agents", "issue-tracker.md")

DOC_RENEWAL_NOTICE = ("Renewed {path} from the current template "
                      "(this file is generated; local edits to it are replaced).")

DOC_CREATED = "created"
DOC_RENEWED = "renewed"
DOC_UNCHANGED = "unchanged"


def _write_if_absent(path, content):
    """Seed a file the project owns from then on, and never touch it again.

    Used for files the tracker merely bootstraps (the `.gitkeep` placeholder):
    once they exist, whatever the project made of them wins.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(content)
        return True
    return False


def _refresh_generated_doc(path, template):
    """Keep a wholly tracker-generated document in sync with its template.

    Unlike `_write_if_absent`, this replaces an existing file. That is only
    defensible for this one document because it is generated in full and
    offers no section for project-local edits: it *is* the description of the
    state machine the engine enforces, so a stale copy would silently instruct
    agents by an obsolete model. Renewal is reported by the caller precisely
    because an edit made here regardless must not vanish unnoticed.

    Returns `DOC_CREATED`, `DOC_RENEWED` or `DOC_UNCHANGED`; an unchanged file
    is not rewritten, which keeps repeated `init` runs silent and idempotent.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        with open(path) as f:
            if f.read() == template:
                return DOC_UNCHANGED
        outcome = DOC_RENEWED
    else:
        outcome = DOC_CREATED
    with open(path, "w") as f:
        f.write(template)
    return outcome


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
    doc_outcome = _refresh_generated_doc(TRACKER_DOC_PATH, TRACKER_DOC)
    _ensure_gitignore_scratch()
    target = _pick_agents_file(args.agents_file)
    wired = _wire_agents_file(target)
    note = "added" if wired else "already present"
    print(f"Issue tracker initialized at {root}/. Agent note in {target} ({note}).")
    if doc_outcome == DOC_RENEWED:
        print(DOC_RENEWAL_NOTICE.format(path=TRACKER_DOC_PATH))


# --------------------------------------------------------------------------- #
# selftest
# --------------------------------------------------------------------------- #

def _selftest_init_renews_tracker_doc(capture):
    """`init` keeps its generated documentation current, and stays idempotent.

    Runs in a throwaway project directory, because `init` writes relative to
    the working directory.
    """
    import tempfile

    renewal_notice = DOC_RENEWAL_NOTICE.format(path=TRACKER_DOC_PATH)
    outer_root = os.environ[ROOT_ENV_VAR]
    previous_cwd = os.getcwd()

    def read(path):
        with open(path) as f:
            return f.read()

    def write(path, content):
        with open(path, "w") as f:
            f.write(content)

    with tempfile.TemporaryDirectory() as project:
        os.chdir(project)
        os.environ[ROOT_ENV_VAR] = os.path.join("docs", "issues")
        try:
            first_run = capture(cmd_init, agents_file=None)
            assert read(TRACKER_DOC_PATH) == TRACKER_DOC
            assert renewal_notice not in first_run, "creation is not a renewal"

            write(TRACKER_DOC_PATH, "documentation of an outdated state model\n")
            placeholder = os.path.join(get_root(), ".gitkeep")
            local_placeholder_content = "kept by the project\n"
            write(placeholder, local_placeholder_content)

            renewing_run = capture(cmd_init, agents_file=None)
            assert read(TRACKER_DOC_PATH) == TRACKER_DOC, "drifted doc not renewed"
            assert renewal_notice in renewing_run, renewing_run
            assert read(placeholder) == local_placeholder_content, \
                "files other than the generated doc keep their previous behaviour"

            # A distinctly old timestamp proves the matching file is not
            # rewritten at all, rather than rewritten with identical bytes.
            untouched_since = 1_000_000_000
            os.utime(TRACKER_DOC_PATH, (untouched_since, untouched_since))
            repeated_run = capture(cmd_init, agents_file=None)
            assert read(TRACKER_DOC_PATH) == TRACKER_DOC
            assert os.path.getmtime(TRACKER_DOC_PATH) == untouched_since, \
                "a matching doc must not be written again"
            assert renewal_notice not in repeated_run, "re-run must stay silent"
        finally:
            os.chdir(previous_cwd)
            os.environ[ROOT_ENV_VAR] = outer_root


def cmd_selftest(_args):
    import tempfile
    from types import SimpleNamespace

    with tempfile.TemporaryDirectory() as tmp:
        os.environ[ROOT_ENV_VAR] = os.path.join(tmp, "docs", "issues")

        def capture(command, **arguments):
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                command(SimpleNamespace(**arguments))
            return buf.getvalue().strip()

        def create(title, parent=None, status=None, blocked_by=None, type=None):
            return capture(cmd_create, title=title, parent=parent, status=status,
                           blocked_by=blocked_by, type=type)

        def set_status(issue, status, reason=None):
            cmd_set_status(SimpleNamespace(issue=issue, status=status,
                                           reason=reason))

        def comments_of(issue_id):
            with open(issue_file(issue_id)) as f:
                return f.read().split("## Comments", 1)[1]

        # A main-issue must declare a type (it maps 1:1 to a branch).
        try:
            create("Typeless main", status="ready-for-agent")
            raise AssertionError("main-issue without --type was allowed")
        except SystemExit:
            pass

        main = create("Checkout redesign", status="ready-for-agent",
                      type="feature")
        assert main == "01-checkout-redesign", main
        assert type_of(main) == "feature", type_of(main)

        a = create("Cart schema", parent=main, status="ready-for-agent")
        b = create("Cart API", parent=main, status="ready-for-agent",
                   blocked_by="1")
        assert type_of(a) == "feature", "child inherits its main-issue's type"
        override = create("Chore slice", parent=main, type="chore")  # needs-triage
        assert type_of(override) == "chore", "child --type overrides inheritance"

        bug = create("Login bug", type="fix")  # a second, top-level main-issue
        assert bug == "02-login-bug", bug
        assert get_status(bug) == "needs-triage" and type_of(bug) == "fix"

        # 'a' is the only ready, unblocked child of main: 'b' is blocked by 'a',
        # 'override' is still needs-triage, and main itself is not a leaf. The
        # actionable frontier therefore cannot hand out work whose premise
        # another agent has yet to establish.
        assert not is_leaf(main) and is_leaf(a) and is_leaf(b)
        assert is_unblocked(a) and not is_unblocked(b)
        assert find_actionable(main) == [a], find_actionable(main)
        assert find_actionable(main, limit=1) == [a]

        # Enforced transitions: needs-triage -> resolved is illegal.
        try:
            set_status(bug, "resolved")
            raise AssertionError("illegal transition was allowed")
        except SystemExit:
            pass

        # A main-issue cannot resolve while a child-issue is open.
        set_status(a, "claimed")
        set_status(a, "resolved")
        assert is_unblocked(b)  # blocker a now resolved
        set_status(main, "claimed")
        try:
            set_status(main, "resolved")
            raise AssertionError("resolved main-issue with open child")
        except SystemExit:
            pass

        # Resolve the remaining children, then the main-issue can resolve.
        set_status(b, "claimed")
        set_status(b, "resolved")
        set_status(override, "ready-for-agent")
        set_status(override, "claimed")
        set_status(override, "resolved")
        set_status(main, "resolved")
        assert get_status(main) == "resolved"

        # A main-issue whose spec collapsed into a single slice (decompose.md's
        # "fold into the main-issue" case) has no child-issues at all. It must
        # still be a leaf `next` can find and hand out directly, and it must
        # still be resolvable — a childless subtree is vacuously fully resolved.
        solo = create("Solo slice main", status="ready-for-agent", type="chore")
        assert is_leaf(solo), "a childless main-issue is a leaf"
        assert find_actionable("") == [solo], find_actionable("")
        set_status(solo, "claimed")
        set_status(solo, "resolved")
        assert get_status(solo) == "resolved"

        # --- superseded: closing an issue that will never be implemented ---

        # The transition demands a reason, and is rejected without one.
        obsolete = create("Obsolete idea", type="feature")  # needs-triage
        try:
            set_status(obsolete, "superseded")
            raise AssertionError("superseded without a reason was allowed")
        except SystemExit:
            pass
        assert get_status(obsolete) == "needs-triage"

        # With a reason it goes through, and the reason lands in the comments.
        set_status(obsolete, "superseded", reason="Subsumed by 05-cart-rewrite.")
        assert get_status(obsolete) == "superseded"
        assert "Subsumed by 05-cart-rewrite." in comments_of(obsolete)

        # Reachable from every open state, including work in progress...
        for open_state in ("needs-triage", "needs-info", "ready-for-agent",
                           "claimed"):
            assert "superseded" in TRANSITIONS[open_state], open_state
        # ...but never from resolved: finished work is not undone afterwards.
        assert "superseded" not in TRANSITIONS["resolved"]

        # The way back out is needs-triage — an issue can turn out to be needed.
        set_status(obsolete, "needs-triage")
        assert get_status(obsolete) == "needs-triage"

        # A superseded blocker releases what it blocks: otherwise an issue that
        # will never be implemented would block its siblings forever.
        dropped_main = create("Dropped slice main", status="ready-for-agent",
                              type="feature")
        dropped = create("Dropped slice", parent=dropped_main,
                         status="ready-for-agent")
        dependent = create("Depends on dropped", parent=dropped_main,
                           status="ready-for-agent", blocked_by="1")
        assert not is_unblocked(dependent)
        set_status(dropped, "superseded", reason="Requirement was withdrawn.")
        assert is_unblocked(dependent), "superseded blocker must release"
        assert find_actionable(dropped_main) == [dependent]

        # A superseded child-issue does not hold up its main-issue's resolution.
        set_status(dependent, "claimed")
        set_status(dependent, "resolved")
        set_status(dropped_main, "claimed")
        set_status(dropped_main, "resolved")
        assert get_status(dropped_main) == "resolved"

        _selftest_init_renews_tracker_doc(capture)

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
    p_create.add_argument("--type", choices=TYPES,
                          help="Change category. Required for a main-issue; a "
                               "child-issue inherits its main-issue's type.")
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
    p_status.add_argument("--reason",
                          help="Justification for the transition, recorded as a "
                               "comment. Required for: "
                               f"{', '.join(sorted(REASON_REQUIRED_STATES))}.")
    p_status.set_defaults(func=cmd_set_status)

    p_comment = sub.add_parser("comment", help="Append a comment.")
    p_comment.add_argument("issue")
    p_comment.add_argument("text")
    p_comment.set_defaults(func=cmd_comment)

    p_next = sub.add_parser("next", help="Print the next actionable child-issue.")
    p_next.add_argument("--parent", help="Restrict to one main-issue's subtree.")
    p_next.add_argument("--all", action="store_true",
                        help="Print every actionable child-issue, one per line, "
                             "instead of only the first. Blocked issues are "
                             "excluded, so the printed issues are independent of "
                             "one another and safe to implement in parallel.")
    p_next.set_defaults(func=cmd_next)

    sub.add_parser("selftest", help="Run the built-in engine tests.").set_defaults(func=cmd_selftest)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
