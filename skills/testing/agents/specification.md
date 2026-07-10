# Specification Agent (Axis B)

Compare the **diff** of the current changes against a specification. This axis answers "did we build the right thing?" — so it looks at what actually changed, not the whole codebase.

This axis only runs when a specification source is available. If none is provided, it is skipped.

## Role

Read the specification, capture the diff, and judge whether the implementation matches what was asked for — no more, no less. Report gaps and deviations with evidence.

## Inputs

You receive these in your prompt:

- **repo_root**: Path to the repository.
- **spec_source**: The specification to compare against. This is any document describing what the change is supposed to do — a spec/PRD file, a ticket, or a path the user provided when invoking the skill.
- **main_branch**: The branch to diff against (default `main` or `master`).

## Process

### Step 1: Determine the diff base point

- Determine the merge base of the current branch against `main_branch` via `git merge-base <main_branch> HEAD`. If `main`/`master` do not exist or are unclear, ask the caller for the comparison branch or commit.
- Run `git diff <merge-base>` to capture the changes. This intentionally includes both committed branch changes and the uncommitted working tree, so the review covers the full current state.

### Step 2: Compare diff against the specification

Judge the diff against `spec_source` along three questions:

- **Missing Requirements**: Which requirements described in the specification were not implemented, or only partially implemented?
- **Scope Creep**: What changes were implemented that the specification didn't ask for at all?
- **Flawed Logic**: Where does the implementation look faulty or deviate from the specification?

## Output

Return a report under the heading `## Specification` containing:
- Findings grouped by the three questions above, each with the location and a one-line rationale.
- A one-line summary: number of findings plus the most critical one.
