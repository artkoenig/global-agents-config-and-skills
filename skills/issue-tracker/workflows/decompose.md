# Workflow: Decompose a specification into issues

Use this workflow when a specification (PRD) exists — either a project-level PRD
or the `## Description` of a parent issue — and it must be turned into
implementable child issues. The specification is the **input**; how it was
authored (via `grill-me-for-spec`, handed over, or written by hand) does not
matter here. This step is a pure transformation: **spec → vertically-sliced child
issues**.

## 1. Locate the parent

Decide where the resulting issues belong:

- If the spec describes a new feature, create a parent issue to hold it:
  ```bash
  python3 <skill>/scripts/tracker.py create --title "<feature name>"
  ```
  Then replace its `## Description` placeholder with the spec's content. This is
  a plain file edit, not a tracker command — only the header and `## Comments`
  are tracker-managed (see
  [reference/issue-format.md](reference/issue-format.md)). If the spec came from
  `grill-me-for-spec` as a standalone file (e.g. `PRD.md`), copy its content in
  and then delete that file: the issue's `## Description` becomes the one copy
  of the spec, not a second one that can drift from it.
- If a parent issue already exists, use its id.

## 2. Slice vertically (tracer bullets)

Break the specification into independently workable child issues using **vertical
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

## 4. Create the child issues

Create each approved slice as a child of the parent, numbered in dependency
order. Because they come from an already-specified parent, they enter directly at
`ready-for-agent`:

```bash
python3 <skill>/scripts/tracker.py create \
  --title "Cart schema" --parent "<parent-id>" --status ready-for-agent
python3 <skill>/scripts/tracker.py create \
  --title "Cart API" --parent "<parent-id>" --status ready-for-agent --blocked-by "01"
```

Then fill each issue's `## Description` and `## Acceptance Criteria`. Keep the
description behavior-focused; avoid hardcoding file paths that go stale.

## 5. Advance the parent

The parent is now fully specified and sliced, so it is no longer awaiting triage.
Move it to `ready-for-agent` so its status reflects reality and its lifecycle can
later reach `resolved` (via `claimed`):

```bash
python3 <skill>/scripts/tracker.py set-status "<parent-id>" ready-for-agent
```

This is a status change on the parent only — `next` still returns just leaf
issues, so implementation is unaffected. The parent stays open until its whole
subtree is `resolved` (enforced by the parent/child rule).

## 6. Handoff

Do not write implementation code here. Tell the user the breakdown is complete and
that implementation can proceed via the [implement workflow](implement.md), which
picks up issues with `next`.
