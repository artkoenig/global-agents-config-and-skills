# Workflow: Resolve an implemented issue

Use this workflow to close out a single issue once it has been fully implemented
and all its tests pass. Do not use it before the work is actually done and
verified — `resolved` means "implemented and passing".

**If the issue will never be implemented, this is the wrong workflow.** An issue
that another issue subsumes, that a merged pull request made obsolete, whose
requirement was dropped, or that is a duplicate is closed as `superseded`
instead — a single command, with a mandatory reason recorded as a comment:

```bash
python3 <skill>/scripts/tracker.py set-status "<issue-id>" superseded \
  --reason "Subsumed by 03-cart-rewrite, which covers the same behavior."
```

That state is reachable from every open state (including `claimed`) but not from
`resolved`, and it counts as closed: it releases blocked siblings and does not
hold up its main-issue's resolution. Never route unbuilt work through `resolved`
to get it off the board — that would record it as implemented. See
[../reference/states.md](../reference/states.md).

## Steps

1. **Record the outcome.** Append a short summary of the solution to the issue's
   `## Comments` (what was built, and anything a future reader should know):
   ```bash
   python3 <skill>/scripts/tracker.py comment "<issue-id>" "Implemented X; see <area>. Tests green."
   ```

2. **If this issue is a main-issue, verify it first.** An issue is a main-issue
   when its id has no `/` — it sits directly under `docs/issues/` rather than
   nested inside another issue. Do not test this by checking whether it has
   child-issues: a main-issue whose specification collapsed into a single slice
   (see decompose.md's "single slice: fold into the main-issue") has none of its
   own, and skipping the four-axis check for it would be wrong — it is still the
   main-issue, and still the one whose subtree gate opens the PR.

   If it is a main-issue, its whole subtree (itself, plus any child-issues) is
   now implemented, and that is exactly the point to run the `testing` skill
   (four-axis verification), once per main-issue, not per child-issue. It should
   already be `claimed` (see [implement.md](implement.md) — a main-issue is
   claimed the moment work starts on any of its child-issues). Pass the
   main-issue's own issue directory as the acceptance-criteria source so Axis B
   reviews the diff against its spec:
   ```
   /testing <issue-tracker-dir>/<issue-id>
   ```
   If it surfaces blocking findings, fix them (or hand them to the user) and
   re-run `testing` — do not resolve a main-issue that hasn't passed
   verification. Child-issues skip this step entirely: they never run the full
   four-axis `testing` skill. During implementation, `issue-implementer`'s own
   Verify step runs only the test suite (via the `test-runner` subagent) against
   that single vertical slice — the Standards and Spec axes run just once, here
   at the main-issue level.

3. **Set the state to resolved:**
   ```bash
   python3 <skill>/scripts/tracker.py set-status "<issue-id>" resolved
   ```
   The tracker rejects this if the issue is a main-issue with open child-issues —
   close the child-issues first, each either `resolved` or `superseded`. A
   main-issue therefore becomes `resolved` only when its whole subtree is closed
   **and**, per step 2, has passed verification.
   Resolving the main-issue is the gate for opening its pull request — one PR for
   the whole main-issue, opened automatically in step 5.

4. **Commit the changes.** Commit the code together with this issue's status
   change, so the tracker state and the work it describes stay in one commit.

   The `issue-implementer` subagent **never commits** — it edits the working
   tree in place and hands its slice back uncommitted (AGENTS.md, git rules), so
   committing is always the main conversation's job, in its own checkout, where
   the "never commit automatically" rule applies:
   - For a **child**-issue resolved while siblings are still open: do not commit
     on your own — report it and let the user decide when to commit. The slice
     stays in the working tree and accumulates with the others on the branch.
   - **Except** at the main-issue resolution gate: when the child being resolved
     is the **last** open issue of the subtree, its resolution is part of the
     gate sequence — commit the accumulated work without asking and proceed
     straight through steps 2–5. Reaching `resolved` authorizes committing,
     pushing, and opening the PR without asking (step 5). Waiting for the user
     here would stall the gate right before it fires: the main-issue can never
     reach `resolved`, and the automatic PR that this gate exists to produce is
     never opened.

5. **Open the pull request — automatically (main-issue only).** Once a
   main-issue is `resolved` and committed, push its `issue/<slug>` branch and
   open the pull request **without a separate ask** — reaching `resolved` is the
   standing authorization for this (AGENTS.md, "Commits & pushes"). Steps 3–5
   plus the last child's resolution commit (step 4) form one uninterrupted
   sequence: do not stop between them to ask whether to commit, push, or open
   the PR. The only legitimate halts are a blocking `testing` finding (step 2)
   and a scope decision the user has left genuinely open. Push every
   local commit first, or the PR misses unpushed work. One PR for the whole
   main-issue; the merge stays manual, and the worktree teardown waits for it. A
   **child**-issue never reaches this step — it has no PR of its own.

6. **Continue.** If more issues remain, pick up the next one with
   `tracker.py next` (see the [implement workflow](implement.md)).
