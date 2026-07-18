- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user experiences it. This makes sure you find the real problem so your fix will actually solve it.
- When starting a new project, use the `grill-me-for-spec` skill to turn the idea into a written specification (PRD) before building.
- Once that PRD exists, decompose it into one main-issue plus child-issues via the `issue-tracker` skill. Issue tracking is **mandatory** for every non-trivial change — do not ask whether to track it, just do it. The only escape hatch is a trivial change, defined deterministically under "Git & Version Control".
- **Ask before code changes.** Never start editing code on your own initiative. When I request work that touches code, confirm scope with me first — for non-trivial work that means filing the issue and confirming its breakdown before implementing; for a trivial change, confirm the one-off intent. (This rule is safeguarded by a behavioral eval; see the `self-test` skill.)
- Critically challenge all requested changes. Before implementing or accepting any modification, verify it against the existing documentation files to ensure consistency and prevent contradictions. Keep documentation always up-to-date.
- When I ask you to investigate a matter, do not make any changes to existing files. Clarify the matter and provide an explanation with a recommendation.
- If you are uncertain during implementation and need to consult the web, place absolute priority on official documentation without exception. Conduct an intensive deep search directly on official developer sites or API references, to find the solution before considering secondary sources (such as forums or blogs).
- Additionally, if your analysis reveals that an already implemented solution in the code can be improved or optimized, proactively suggest these improvements.
- Keep your responses in the main conversation precise and short. State findings, decisions, and what changed — skip recaps, restated file contents, and step-by-step narration. Push detail into subagent reports, files, or tool output instead of the conversation; this conserves context.


## Cloud Session Bootstrap Trigger

**Trigger**: At the start of any session, in any git repository I own, before
other work begins (including before the branch decision below). A repo is
mine if it has no remote yet, or its `origin` points to `github.com` under
the `artkoenig` account — anything else (a work, client, or third-party repo)
is out of scope; skip it silently, don't ask.
**Action**: Check whether three things are in place: (a) `.claude/hooks/session-start.sh`
is installed and matches the `cloud-session-bootstrap` skill's canonical
version, (b) `.claude/hooks/worktree_guard.py` is installed and current, with
`.claude/settings.json` wiring it into `hooks.PreToolUse` and setting
`worktree.baseRef` to `"head"` — this is what enforces the "Worktree Isolation"
rule below, not just documents it, so a session missing it silently loses that
enforcement — and (c) `core.hooksPath` points at this config repo's `.githooks`
so the deterministic `pre-push` checks are active. The checks themselves are
never copied into other repos — a target repo's `core.hooksPath` points at this
config repo's (or, in cloud sessions, its clone's) `.githooks`, and the hook
locates its checker relative to itself. If any of the three is missing or has
drifted, run the `cloud-session-bootstrap` skill to install/update it. This is
mandatory by default for every repo of mine — not something to wait for me to
ask for. Once set, the `pre-push` checks apply to every worktree automatically,
since all worktrees share one `.git`.

## Git & Version Control

Decide the branch **once**, at the very start of a task, before any research,
`grill-me-for-spec` session, or implementation begins — not something to
revisit once work is underway. In your own checkout:
- Check whether the target files are versioned.
- Check for untracked files (`git status`). If any exist, ask me whether they
  should be committed or discarded before proceeding — don't decide either
  way yourself.
- Print the current branch name and ask me whether to use it or create a new
  one.
- Before creating a new branch, check out main/master first and make sure it's
  up to date with origin.
- If changes are requested on a branch that already has an open or recently
  completed PR, ask me whether to start a new branch instead of reusing the
  old one.

Branch naming: every work branch is `issue/<slug>` and maps 1:1 to exactly one
top-level issue ("main-issue"). This is the **only** valid branch pattern — the
old `feature|fix|refactor|chore` prefixes are gone; that category now lives in a
`type` field inside the issue's `issue.md` (`feature|fix|refactor|chore`). The
`pre-push` hook rejects any branch name that doesn't match `^issue/[a-z0-9-]+$`
(see `scripts/git_workflow_rules.py`).

The relationship is strict: **1 main-issue = 1 branch `issue/<slug>` = 1
worktree = 1 pull request.** The PR is opened only once every child-issue of the
main-issue is resolved. `main` is never pushed to locally — it advances only
through a GitHub PR merge, and the hook rejects any push whose target ref is
`main`.

**Trivial exception.** A change is trivial — and may skip issue tracking and its
own branch — only if it meets the deterministic criterion in
`is_trivial_change` (`scripts/git_workflow_rules.py`): **exactly one changed
file AND (at most one added line OR the file's extension is one of `.md`,
`.json`, `.yaml`, `.yml`, `.txt`)**. A trivial change rides on the currently
checked-out branch; it is never committed directly onto `main`.

Once that branch is checked out, everything downstream rides on it without
re-deciding: research, `grill-me-for-spec`, decomposing into issues, and
implementation. Implementation itself happens in worktrees seeded from this
branch (see Worktree Isolation below) — no (sub)agent doing the actual coding
ever has to reason about which branch it's on; you, the main conversation,
merge their worktree branches back into it.

Commits & pushes, in your own checkout:
- Never commit or push automatically — only when I explicitly ask. The one
  standing exception is the main-issue resolution gate: reaching `resolved`
  (whole subtree done, `testing` green) is itself the authorization to commit,
  push, and open the PR for that main-issue — see the automatic-PR bullet below.
- Never add a `Co-Authored-By:` trailer of any kind. This is a
  single-maintainer repo with no allow-list; the `pre-push` hook rejects any
  pushed commit whose message carries one.
- If orphaned or merged branches exist, ask me before deleting them.
- Before creating a PR, make sure every local commit is actually pushed to its
  remote branch — a PR opened against a stale remote silently misses whatever
  hasn't been pushed yet.
- **Automatic PR at resolution.** When a main-issue reaches `resolved`, push its
  `issue/<slug>` branch and open the pull request automatically — no separate
  ask; this standing rule *is* the authorization carved out above. Only the PR
  is automated: the merge stays manual, and the worktree teardown (see "Worktree
  Isolation") waits for that merge. This never applies to a child-issue — those
  never get their own PR.

The "ask me" steps above assume a human is present to answer, which is why
they're resolved upfront in the main conversation — subagents never see them.
The one written exception: a subagent running with `isolation: worktree`
(e.g. `issue-implementer`) commits its own work without asking, because an
uncommitted worktree can't be handed back any other way. That exception
covers committing inside that worktree only — never pushing, and never the
merge step back in the main checkout, where the rules above apply in full.

## Worktree Isolation

Every work session runs in an isolated git worktree, entered at the **start**
of the session — as soon as it's clear the session will touch the repo, before
research or implementation begins, not deferred until the first edit. Only two
things stay in the checkout: a pure investigation/Q&A session that makes no
changes (the "investigate = don't touch files" rule above), and a trivial
change as defined under "Git & Version Control". If a session that began as
investigation turns into work, enter the worktree at that point.

**This rule is enforced, not just documented.** Unlike the branch-name/
co-author rules under "Git & Version Control", whether an edit happened inside
a worktree leaves no trace in the finished commit for a `pre-push` hook to
check afterward — so it kept eroding as unverified guidance. A `PreToolUse`
hook (`worktree_guard.py`, installed by `cloud-session-bootstrap`) now denies
an `Edit`/`Write`/`NotebookEdit` call that would make a non-trivial change
directly in the main checkout, before it happens. It approximates the trivial
criterion below (it cannot see a diff that hasn't happened yet, so it is
conservative: only a single file with a docs/config extension passes) and
exempts the issue tracker's own directory, since `decompose.md`/`implement.md`
write and merge `issue.md` files directly in the checkout by design. It does
not see `Bash`-driven file writes — that gap is deliberate, not a sandbox. If
I've explicitly said to work directly in the checkout for a task, touch
`.claude/.worktree-bypass` to disable it for that session.

Once the branch above is selected, code-writing work — direct or delegated —
happens in that worktree, never in the checkout itself:
- **Delegating**: give any code-writing subagent `isolation: worktree` —
  already the default for `issue-implementer`.
- **Working directly** (no subagent involved): you are already in the session's
  worktree from the rule above; if not (e.g. the change looked trivial but
  grew), create one now under `.worktrees/` (`git worktree add .worktrees/<slug>
  <branch>`) and continue the work there, unless the change meets the trivial
  criterion under "Git & Version Control" or I've said to work directly in the
  current checkout.

**Use `.worktrees/`, not the native worktree tool.** Create these main-issue
worktrees with `git worktree add .worktrees/<slug>` — do **not** use Claude
Code's `EnterWorktree` or `--worktree`. Those put the worktree under
`.claude/worktrees/`, outside this repo's `.worktrees/` convention and its
`.gitignore` entry, where it pollutes the main checkout's status. `.worktrees/`
is the only sanctioned location for a main-issue worktree.

`worktree.baseRef` must stay set to `"head"` in Claude Code's settings for
the delegated `isolation: worktree` path to work: it's what makes a new worktree
branch from whatever you just
checked out above instead of the repository's default branch. Without it,
every worktree would silently restart from `main`, ignoring the branch
decided upfront — which is exactly the branch-awareness problem this section
exists to remove from implementation.

**Exception — read-only research/review/test subagents**
(`spec-researcher`, `standards-reviewer`, `spec-reviewer`, `test-runner`): do
**not** isolate these. Their whole job is to judge the actual current state,
uncommitted changes included (`spec-reviewer` diffs against the working tree
by design, `test-runner` runs the suite as it sits on disk) — a worktree only
ever reflects committed history, so isolating them would make them silently
judge a stale snapshot instead of what's really there.

**Two-level worktree layout.** Worktrees exist at two nested levels:

- *Main-issue level (you manage this).* Several main-issues can run locally at
  the same time — each in its own worktree under `.worktrees/`, driven by its
  own independent Claude Code session. There is no shared orchestrator between
  those sessions; only the shared `.git` connects them. `.worktrees/` is listed
  in `.gitignore` and is never committed. **Teardown:** a main-issue's worktree
  lives exactly as long as its pull request. Once that PR is **merged** —
  never earlier, since a review may still send changes back to this worktree —
  tear it down with `git worktree remove .worktrees/<slug>` from the main
  checkout (you cannot remove the worktree you are standing in). Then sweep any
  child
  worktrees that a merge left behind (`git worktree list`, remove the
  stragglers, `git worktree prune`), so no worktree outlives the main-issue it
  belonged to.
- *Child-issue level (the session manages this).* Within one main-issue's
  session, its child-issues are implemented in parallel by `issue-implementer`
  subagents (`isolation: worktree`). They merge **sequentially, in dependency
  order** (from `tracker.py`) into the main-issue branch. After each merge the
  child worktree is removed (`git worktree remove`); no lasting child branches
  are left behind.

Register every worktree flat against the shared `.git` so nesting never
produces `.worktrees/.worktrees/`.

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

This delegation policy is safeguarded by a behavioral eval (see the
`self-test` skill), which checks that the documented delegation choices
actually happen.

## Engineering Principles Trigger

**Trigger**: BEFORE making architectural decisions, choosing frameworks/libraries, defining module or component boundaries, planning/executing cross-module refactoring, OR writing, editing, generating, or refactoring any code files or unit tests.
**Action**: You MUST read and follow the `engineering-principles` skill.

This trigger is safeguarded by a behavioral eval (see the `self-test`
skill), which checks that a code-touching request actually causes the
`engineering-principles` skill to be read before the code is written.

## Running the Agent self-tests manually

The self-testing apparatus (see the `self-test` skill) verifies the integrity of this repository.

1. **Deterministic checks** — instant, no LLM. The quick default:

   ```bash
   python3 -m unittest discover -s scripts -p 'test_*.py'
   ```
   These deterministic checks also run automatically via the `pre-push` hook. A failure blocks the push; `git push --no-verify` is the sanctioned override.

2. **Behavioral evals** — full agentic workflow; slower.
   Behavioral evals verify whether skills, subagents, and AGENTS.md rules actually behave as documented. Since they require headless Agent executions, they are run entirely via the `self-test` skill rather than as a git hook.
   To run them, simply ask the agent: "run the self-test skill" or "run behavioral evals".
