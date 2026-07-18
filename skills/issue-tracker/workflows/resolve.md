# Workflow: Resolve an implemented issue

Use this workflow to close out a single issue once it has been fully implemented
and all its tests pass. Do not use it before the work is actually done and
verified — `resolved` means "implemented and passing".

## Steps

1. **Record the outcome.** Append a short summary of the solution to the issue's
   `## Comments` (what was built, and anything a future reader should know):
   ```bash
   python3 <skill>/scripts/tracker.py comment "<issue-id>" "Implemented X; see <area>. Tests green."
   ```

2. **If this issue is a main-issue, verify it first.** Check whether it has
   child-issues:
   ```bash
   python3 <skill>/scripts/tracker.py list --parent "<issue-id>"
   ```
   Any results mean this is a main-issue, not a child-issue — its whole subtree
   is now implemented, and that is exactly the point to run the `testing` skill
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
   resolve the child-issues first. A main-issue therefore becomes `resolved` only
   when its whole subtree is done **and**, per step 2, has passed verification.
   Resolving the main-issue is the gate for opening its pull request — one PR for
   the whole main-issue, opened automatically in step 5.

4. **Commit the changes.** Commit the code together with this issue's status
   change, so the tracker state and the work it describes stay in one commit.

   *Who commits depends on where you are*, per AGENTS.md's git rules:
   - Working **in your own worktree** (the `issue-implementer` subagent): commit
     without asking. Your worktree cannot be handed back otherwise. Never push.
   - Working **in the user's checkout**: do not commit on your own — **except**
     at the main-issue resolution gate, where reaching `resolved` authorizes
     committing, pushing, and opening the PR without asking (step 5). For a
     resolved **child**-issue in the user's checkout, report it and let the user
     decide when to commit.

5. **Open the pull request — automatically (main-issue only).** Once a
   main-issue is `resolved` and committed, push its `issue/<slug>` branch and
   open the pull request **without a separate ask** — reaching `resolved` is the
   standing authorization for this (AGENTS.md, "Commits & pushes"). Push every
   local commit first, or the PR misses unpushed work. One PR for the whole
   main-issue; the merge stays manual, and the worktree teardown waits for it. A
   **child**-issue never reaches this step — it has no PR of its own.

6. **Continue.** If more issues remain, pick up the next one with
   `tracker.py next` (see the [implement workflow](implement.md)).
