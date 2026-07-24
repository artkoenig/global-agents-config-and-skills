# Workflow: Plan a main-issue's implementation at module level

Run this **once per main-issue**, after [decompose.md](decompose.md) has sliced
the spec into child-issues and **before** [implement.md](implement.md) dispatches
any implementer. It produces the shared module-level plan that every sequential
slice is built against, and gut-checks that plan with an independent clean-room
design before a line of code is written.

Why it sits here: child-issues are implemented **sequentially and in isolation** —
each `issue-implementer` sees only its own slice. Without a plan agreed up front,
each slice invents its own module boundaries and shared types, and they drift.
This step decides those boundaries once, by an agent that saw the whole
main-issue.

The plan lives in a **temporary** `design.md` in the main-issue's directory. It
is a working artifact, not part of the deliverable: it is deleted at the
resolution gate ([resolve.md](resolve.md)) so it never enters the PR — which is
also why it does **not** violate the "issue docs stay solution-free" rule
([../reference/issue-format.md](../reference/issue-format.md)). The behaviour spec
stays in `issue.md`; the technical plan stays in `design.md`, and then it is gone.

Resolve `<skill>` below to the path of the `issue-tracker` skill's script.

## When to run it — and when to skip

- **Main-issue with child-issues** → run it. The more slices, the more the shared
  contracts matter, and the more a sequential implementer benefits from a plan it
  did not have to reconstruct on its own.
- **Single-slice main-issue** (decompose folded one slice into the main-issue, so
  it has no child-issues — see decompose.md's "single slice: fold into the
  main-issue") → usually **skip**: with one slice there are no cross-slice
  boundaries to agree. Run it only if that single slice itself spans several
  modules and a plan would genuinely help.

## 1. Produce the module plan — `solution-architect`

Dispatch one `solution-architect` subagent with:

- **main_issue_id** — the main-issue id (no `/`).
- **tracker_script** — the resolved path to `scripts/tracker.py`.

It reads the whole main-issue (spec + every child's acceptance criteria), grounds
itself in `CONTEXT.md`, the ADRs and the current code, and writes
`docs/issues/<main-id>/design.md`: a module map, the public contracts the slices
exchange, the slice-to-module mapping, key decisions, ADR candidates and risks.
It writes **only** `design.md` — it does not touch code or the issue files. When
it returns, note its module map, its ADR candidates and its risks. Do not restate
its rules here; its definition carries them.

## 2. Gut-check the plan — clean-room review

Do not take the plan on trust. Run the
[clean-room-review](../../clean-room-review/SKILL.md) skill to get an
**independent** design of the *same problem* from an expert who never sees the
architect's plan or the code:

- Frame the neutral brief from the main-issue's **problem** — the goal and the
  hard constraints only. Do **not** put the architect's `design.md`, the current
  code, or any proposed approach into the brief; that would contaminate the clean
  room (clean-room-review neutrality rule 1). Give the raw data and its shape, not
  the architect's derived design.
- Run the reviewer's question/answer loop and receive its blind proposal.
- **Reconcile** it against `design.md`:
  - Where the clean-room design **agrees** with the plan → independent
    confirmation the boundaries are sound.
  - Where it **improves** on the plan → update `design.md` to adopt it.
  - Where it is **impractical** against real constraints the reviewer could not
    see → keep the plan, and note the constraint.

Edit `design.md` in place to reflect the reconciliation. If the gut-check
overturns something big, that is exactly the cheap moment to fix it — before any
slice is built on it. This clean-room pass is the plan's review; it stands in for
the user sign-off that the decompose breakdown gets, because a subagent-authored
plan is checked by an independent design, not by the author.

## 3. Record genuine ADRs — with the user

If the architect flagged an **ADR candidate** and the clean-room step did not
knock it down, record it as an ADR under `docs/adr/` (see the ADR format), with
the user in the main conversation — a settled, hard-to-reverse decision is a
main-conversation call, not a throwaway line in `design.md`. Unlike `design.md`,
an ADR **persists**: it is committed and outlives the plan. Then reference it from
`design.md`. If there are no ADR candidates, skip this step.

## 4. Handoff

The plan is ready. Proceed to [implement.md](implement.md): each
`issue-implementer` reads `docs/issues/<main-id>/design.md` and builds its slice
against the module boundaries and contracts it defines. At the resolution gate,
the `review` skill's Axis E (Design-Conformance) checks the finished diff back
against this same `design.md` — did the implementation honour the plan? — which is
why the clean-room independence is spent here, up front, on the plan itself. The
`design.md` stays in the working tree, uncommitted, for the whole implementation,
and is deleted at the main-issue resolution gate (resolve.md step 4, after that
review) so it never lands in the PR.
