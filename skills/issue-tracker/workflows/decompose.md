# Workflow: Decompose a specification into issues

Use this workflow when a specification (PRD) exists — held in a **main-issue's**
`## Description` — and it must be turned into implementable child-issues. The
specification is the **input**; how it was authored (via `grill-me-for-spec`,
handed over, or written by hand) does not matter here. This step is a pure
transformation: **spec → vertically-sliced child-issues**, all belonging to that
one main-issue = one branch = one PR.

## 1. Locate the main-issue

The spec belongs to exactly one **main-issue** — the top-level issue that maps
1:1 to this branch, worktree and pull request.

- Usually `grill-me-for-spec` has already created it (with its `Type:`) and put
  the PRD in its `## Description`. Use that id.
- If it does not exist yet, create it, choosing the change category as its type:
  ```bash
  python3 <skill>/scripts/tracker.py create --title "<main-issue name>" --type feature
  ```
  Then replace its `## Description` placeholder with the spec's content. This is
  a plain file edit, not a tracker command — only the header and `## Comments`
  are tracker-managed (see
  [reference/issue-format.md](reference/issue-format.md)). If the spec exists
  only as a standalone file (a hand-written `PRD.md`, or one handed over from
  elsewhere — `grill-me-for-spec` no longer leaves one, it fills the main-issue
  directly), copy its content in and then delete that file: the main-issue's
  `## Description` becomes the one copy of the spec, not a second one that can
  drift from it.

## 2. Slice vertically (tracer bullets)

Break the specification into independently workable child-issues using **vertical
slices**: each slice cuts through all affected layers (schema, API, UI, tests)
and delivers a minimal, independently demonstrable, verifiable behavior. Define
any prefactoring as the first issues.

Avoid horizontal slices (e.g. "do all the database work") — they cannot be
demonstrated on their own and create long blocker chains.

## 3. Review the breakdown with the user

Before creating anything, present the proposed list in chat. For each issue show:

- **Title** — a short, concise name
- **Blocked by** — which sibling issues must complete first
- **Behavior** — the end-to-end behavior it delivers

Ask the user:
- Is the granularity right?
- Are the dependencies correct?
- Should any issues be merged or split further?

Only proceed once the user approves.

## 4. Create the child-issues

Create each approved slice as a child of the main-issue, **numbered in dependency
order**. Because a child can only block a sibling that already exists, numbering
in dependency order makes numeric order a valid merge order later (see
[implement.md](implement.md)). Children inherit the main-issue's type, so
`--type` is only needed to override it. Because they come from an
already-specified main-issue, they enter directly at `ready-for-agent`:

```bash
python3 <skill>/scripts/tracker.py create \
  --title "Cart schema" --parent "<main-id>" --status ready-for-agent
python3 <skill>/scripts/tracker.py create \
  --title "Cart API" --parent "<main-id>" --status ready-for-agent --blocked-by "01"
```

Then fill each issue's `## Description` and `## Acceptance Criteria`. Keep the
description behavior-focused; avoid hardcoding file paths that go stale.

## 5. Advance the main-issue

The main-issue is now fully specified and sliced, so it is no longer awaiting
triage. Move it to `ready-for-agent` so its status reflects reality and its
lifecycle can later reach `resolved` (via `claimed`):

```bash
python3 <skill>/scripts/tracker.py set-status "<main-id>" ready-for-agent
```

This is a status change on the main-issue only — `next` still returns just
child-issues, so implementation is unaffected. The main-issue stays open until
its whole subtree is `resolved` (enforced by the main-issue/child-issue rule).

## 6. Handoff

Do not write implementation code here. Tell the user the breakdown is complete and
that implementation can proceed via the [implement workflow](implement.md), which
picks up child-issues with `next`.

Note the handoff prerequisite: the child-issues just created under `docs/issues/`
are still uncommitted. Before implement.md's parallel dispatch can spawn
`issue-implementer` worktrees, this issue documentation **must be committed** —
a worktree branches from committed history and cannot otherwise read its own
`issue.md` (see implement.md, Section A, step 3).
