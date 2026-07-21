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

If this slicing produces only a **single** slice, there is nothing to slice —
say so plainly instead of proposing a lone child-issue, and go to
[Step 3a](#3a-single-slice-fold-into-the-main-issue) instead of Step 3.

## 3. Review the breakdown with the user

Before creating anything, present the proposed list in chat. For each issue show:

- **Title** — a short, concise name
- **Blocked by** — which sibling issues must complete first
- **Behavior** — the end-to-end behavior it delivers

Ask the user:
- Is the granularity right?
- Are the dependencies correct?
- Should any issues be merged or split further?

Only proceed once the user approves, then go to [Step 4](#4-create-the-child-issues).

## 3a. Single slice: fold into the main-issue

A single child-issue is not a slice of anything — it would just carry the whole
main-issue's implementation one directory deeper for no benefit, and the tracker
would still enforce a main-issue/child-issue rule for a "subtree" of one. Skip
creating a child-issue and hold the implementation in the main-issue itself
instead:

- Replace the main-issue's `## Acceptance Criteria` placeholder directly with
  the slice's observable, verifiable criteria (the `## Description` already
  holds the spec from Step 1).
- Confirm this with the user the same way Step 3 would — show the criteria and
  ask whether it looks right — then skip Step 4 entirely and go straight to
  [Step 5](#5-advance-the-main-issue). There is no child-issue to create.

The main-issue itself becomes the sole unit of work: with no child-issues, the
engine already treats it as a leaf (see
[implement.md](implement.md#c-single-slice-main-issue-no-child-issues) for how
it gets implemented and resolved).

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

Then fill each issue's `## Description` and `## Acceptance Criteria`. Because each
`issue.md` was just created, read it before editing it — the `Write` tool only
overwrites a file already read this session. Keep the description
behavior-focused; avoid hardcoding file paths that go stale.

(This step only applies when Step 2 produced more than one slice. For exactly
one slice, Step 3a already handled it and there is no child-issue to create
here.)

## 5. Advance the main-issue

The main-issue is now fully specified and sliced, so it is no longer awaiting
triage. Move it to `ready-for-agent` so its status reflects reality and its
lifecycle can later reach `resolved` (via `claimed`):

```bash
python3 <skill>/scripts/tracker.py set-status "<main-id>" ready-for-agent
```

If it has child-issues, this is a status change on the main-issue only —
`next --parent <main-id>` still returns just those child-issues, so their
implementation is unaffected. The main-issue stays open until its whole subtree
is closed — every child-issue `resolved`, or `superseded` if a slice turns out
never to be needed (enforced by the main-issue/child-issue rule).

If slicing this main-issue makes an **existing** issue redundant — the new
slices subsume it, or it turns out to be a duplicate — close that issue as
`superseded` rather than leaving it open with a cross-reference comment:

```bash
python3 <skill>/scripts/tracker.py set-status "<obsolete-id>" superseded \
  --reason "Subsumed by <main-id>/02-cart-api, which covers the same behavior."
```

The reason is mandatory and is recorded as a comment on that issue. See
[../reference/states.md](../reference/states.md).

If Step 3a folded a single slice into it instead, it now has **no**
child-issues, so it is itself a leaf: an unscoped `next` (run without
`--parent`) can return the main-issue id directly, per implement.md's
[single-slice section](implement.md#c-single-slice-main-issue-no-child-issues).

## 6. Handoff

Do not write implementation code here. Tell the user the breakdown is complete.

- **More than one slice**: implementation proceeds via the
  [implement workflow](implement.md), which picks up child-issues with `next`.
- **A single slice folded into the main-issue (Step 3a)**: implementation
  proceeds directly on the main-issue id — see implement.md's
  [single-slice section](implement.md#c-single-slice-main-issue-no-child-issues).

Note the handoff prerequisite: the issue documentation just written under
`docs/issues/` (the new child-issues, or the main-issue's own updated
`## Acceptance Criteria` in the single-slice case) is still uncommitted. Before
implement.md's parallel dispatch can spawn `issue-implementer` worktrees, this
documentation **must be committed** — a worktree branches from committed
history and cannot otherwise read its own `issue.md` (see implement.md,
Section A, step 3).
