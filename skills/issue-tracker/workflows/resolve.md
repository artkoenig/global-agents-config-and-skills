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

2. **Set the state to resolved:**
   ```bash
   python3 <skill>/scripts/tracker.py set-status "<issue-id>" resolved
   ```
   The tracker rejects this if the issue is a parent with open children — resolve
   the children first. A feature therefore becomes `resolved` only when its whole
   subtree is done.

3. **Continue.** If more issues remain, pick up the next one with
   `tracker.py next` (typically via the `implement-with-ticket` skill).
