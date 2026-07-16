- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user experiences it. This makes sure you find the real problem so your fix will actually solve it.
- When starting a new project, use the `grill-me-for-spec` skill to turn the idea into a written specification (PRD) before building.
- Once that PRD exists, ask whether to set up issue tracking and break it into issues via the `issue-tracker` skill.
- When a project has issue tracking set up (a `docs/issues/` directory exists, or `ISSUE_TRACKER_DIR` is set), do not begin code changes before asking me whether to create an issue for the work first. If I say yes, file it via the `issue-tracker` skill and proceed through the tracked workflow; if I decline, implement directly.
- Critically challenge all requested changes. Before implementing or accepting any modification, verify it against the existing documentation files to ensure consistency and prevent contradictions. Keep documentation always up-to-date.
- When I ask you to investigate a matter, do not make any changes to existing files. Clarify the matter and provide an explanation with a recommendation.
- If you are uncertain during implementation and need to consult the web, place absolute priority on official documentation without exception. Conduct an intensive deep search directly on official developer sites or API references, to find the solution before considering secondary sources (such as forums or blogs).
- Additionally, if your analysis reveals that an already implemented solution in the code can be improved or optimized, proactively suggest these improvements.
- Keep your responses in the main conversation precise and short. State findings, decisions, and what changed — skip recaps, restated file contents, and step-by-step narration. Push detail into subagent reports, files, or tool output instead of the conversation; this conserves context.


## Git & Version Control

Applies immediately, at the start of any task, whenever the files involved are
tracked in a git repository — before any search, directory listing, or file
read.

In your own checkout, before making any changes:
- Check whether the target files are versioned.
- Print the current branch name and ask me whether to use it or create a new
  one.
- Before creating a new branch, check out main/master first and make sure it's
  up to date with origin.
- If changes are requested on a branch that already has an open or recently
  completed PR, ask me whether to start a new branch instead of reusing the
  old one.

Naming a new branch: `<type>/<short-kebab-slug>`, where `<type>` is one of:
- `feature/` — new functionality
- `fix/` — bug fixes
- `refactor/` — restructuring with no behavior change
- `chore/` — tooling, config, docs, dependencies, or other maintenance

The one exception is the `issue-tracker` workflow, which names branches
`issue/<slug-of-issue-id>` instead — that ties the branch 1:1 back to a tracker
id, which the `<type>/` scheme can't express. Don't rename those.

Commits & pushes, in your own checkout:
- Never commit or push automatically — only when I explicitly ask.
- Never add an agent name as commit co-author.
- If orphaned or merged branches exist, ask me before deleting them.

The "ask me" steps above assume a human is present to answer. **Subagents
cannot ask** (no `AskUserQuestion`) and never apply those steps directly —
they follow whatever explicit instructions their own definition gives them
instead. The one written exception: a subagent running with `isolation:
worktree` (e.g. `issue-implementer`) commits its own work without asking,
because an uncommitted worktree can't be handed back any other way. That
exception covers committing inside that worktree only — never pushing, and
never the merge step back in the main checkout, where the rules above apply
in full.

## Delegation to subagents

Keep the main conversation's context for the things that need me in it. Delegate
work whose *output* matters but whose *process* does not — exploration,
implementation, verification — to a subagent, and expect a summary back rather
than files, logs, or diffs.

- **Codebase research** (during `grill-me-for-spec`, or any "how does this work
  today?" question spanning more than a handful of files) → `spec-researcher`.
- **Implementing a tracked issue** → `issue-implementer`, one per issue id. Use
  `tracker.py next --all` to get the parallel-safe set and dispatch several at
  once; each works in its own worktree and returns a branch to merge.
- **Verification** → the `testing` skill, which fans out to `standards-reviewer`,
  `spec-reviewer` and `test-runner`.

Do not delegate anything that has to ask me something — subagents have no way to
put a question to me and will invent the answer instead. The grilling in
`grill-me-for-spec`, the breakdown review when decomposing a spec, the branch
question in the git rules above, triage, and every decision I have reserved for
myself stay in the main conversation.

Do not delegate trivial or single-file work either. A subagent that costs more to
brief than to do is a loss, not a saving.

## Engineering Principles Trigger

**Trigger**: BEFORE making architectural decisions, choosing frameworks/libraries, defining module or component boundaries, planning/executing cross-module refactoring, OR writing, editing, generating, or refactoring any code files or unit tests.
**Action**: You MUST read and follow the `engineering-principles` skill.
