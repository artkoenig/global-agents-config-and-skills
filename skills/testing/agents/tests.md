# Tests Agent (Axis C)

Run the project's test suite and report whether it is green. This axis answers "does it still work?" — the empirical counterpart to the two review axes.

## Role

Find the right test command, run it, and report the result clearly. A failing suite is a real problem, so surface the failing output rather than just a red/green flag.

## Inputs

You receive these in your prompt:

- **repo_root**: Path to the repository.
- **test_command_file**: Path to `.scratch/test-command.txt` (may be absent).

## Process

### Step 1: Determine the test command

- Read the test command from `test_command_file` if it exists.
- If not present, infer it from the project root — for example `package.json` -> `npm test` or `vitest`; `Cargo.toml` -> `cargo test`; `requirements.txt` -> `pytest`.
- If it cannot be clearly determined, ask the caller once for the test command and save it to `test_command_file` so future runs are deterministic.

### Step 2: Run the suite

- Execute the test command and confirm that **all** tests pass (are green).
- A failing test is a **blocking** failure: capture the failing output so it can be resolved. Report the specific failures, not just the fact that the suite is red.

## Output

Return a report under the heading `## Tests` containing:
- The command that was run.
- Green/red status, with the failing test output included when red.
- A one-line summary of the result.
