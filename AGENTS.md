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
- **Ground every analytical claim in verified sources — never in estimation.** When you analyze code, data, files, or any other source, do not state findings, numbers, behaviors, or conclusions you have not actually confirmed by reading that source. Guessing, extrapolating from a filename or a variable name, answering from memory, and then revising the statement once you've finally looked is exactly the failure this rule forbids. The order is fixed: read the file, run the query, check the reference **first**, then state the conclusion — never the other way around. If a definitive answer would require verification you haven't yet done, do the verification rather than skip it; if that is genuinely impossible in the moment, label the statement explicitly as an unverified assumption or hypothesis and never present it as established fact. A single confident-but-wrong claim that has to be walked back costs more trust than the extra minute of checking would have cost.
- **Answer short, plain, and concrete — this is a hard rule, not a preference.** Every reply in the main conversation must be:
  - **Short.** State only the findings, the decision, and what changed. No recaps, no restating file contents, no step-by-step narration of what you did. If a point doesn't change what I know or decide, cut it.
  - **Plain.** Everyday language, short sentences. No jargon, no filler, no convoluted phrasing where a simpler wording works. Being short must never make the answer hard to follow — if brevity would cost clarity, keep the clarity and cut something else.
  - **Concrete.** Whenever it helps me follow your reasoning, back a claim with the actual evidence from the source — the specific file and line, the real value, the exact query result, a short quote. Don't just tell me *that* something is the case; show me the piece of data that proves it, so I can check it myself. This ties directly into the "ground every analytical claim in verified sources" rule above: the same evidence you verified against is what you cite.
  - Push long detail — full logs, diffs, file dumps, exhaustive reasoning — into subagent reports, files, or tool output, never into the conversation. This keeps the reply readable and conserves context.


## Cloud Session Bootstrap Trigger

**Trigger**: At the start of any session, in any git repository I own, before
other work begins (including before the branch decision below). A repo is
mine if it has no remote yet, or its `origin` points to `github.com` under
the `artkoenig` account — anything else (a work, client, or third-party repo)
is out of scope; skip it silently, don't ask.
**Action**: Check whether three things are in place: (a) `.claude/hooks/session-start.sh`
is installed and matches the `cloud-session-bootstrap` skill's canonical
version, (b) `.claude/hooks/worktree_guard.py` and
`.claude/hooks/worktree-create.sh` are installed and current, with
`.claude/settings.json` wiring the guard into `hooks.PreToolUse`, the redirect
into `hooks.WorktreeCreate`, and setting
`worktree.baseRef` to `"head"` — this is what enforces the **local-only**
"Worktree Isolation" rule below, not just documents it, so a session missing it
silently loses that enforcement (the guard) or lets native worktrees escape to
`.claude/worktrees/` (the redirect). The guard no-ops in cloud sessions
(`CLAUDE_CODE_REMOTE=true`), where the per-session clone already provides the
isolation, so it is still installed everywhere but only bites locally — and
(c) `core.hooksPath` points at this config repo's `.githooks`
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

Branch naming: the recommended name for a work branch is `issue/<slug>`,
mapping 1:1 to exactly one top-level issue ("main-issue"). The old
`feature|fix|refactor|chore` prefixes are gone; that category now lives in a
`type` field inside the issue's `issue.md` (`feature|fix|refactor|chore`). This
is a convention, not a gate: the `pre-push` hook no longer enforces a branch
name. Cloud (Claude Code on the web) sessions run on a platform-assigned branch
(e.g. `claude/<slug>`) that the session cannot rename, so enforcing `^issue/`
would reject every remote push (see `scripts/git_workflow_rules.py`).

The relationship is strict: **1 main-issue = 1 branch `issue/<slug>` = 1 pull
request** — and, in local sessions only, = 1 worktree (see "Worktree
Isolation"; cloud sessions skip the worktree, working directly on the branch in
their own clone). The PR is opened only once every child-issue of the
main-issue is closed — `resolved`, or `superseded` for one that will never be
implemented. `main` is never pushed to locally — it advances only
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
implementation. Child-issues are implemented **sequentially, one after another,
directly on this branch** — locally inside the session's main-issue worktree,
in cloud sessions directly in the per-session clone (see Worktree Isolation
below). No (sub)agent doing the actual coding has to reason about which branch
it's on: the `issue-implementer` you delegate to edits this same working tree in
place, one slice at a time, and hands each slice back — there are no per-child
worktree branches to merge.

Commits & pushes, in your own checkout:
- Never commit or push automatically — only when I explicitly ask.
- **Equal-rank exception, not a footnote: the main-issue resolution gate.**
  The moment the last child-issue of a main-issue closes and `review` is
  green, the prohibition above stops applying to that main-issue. From there,
  child-resolution commit → main-issue `resolved` → commit → push → open PR is
  **one uninterrupted sequence — no question to me anywhere in it**. Stopping
  to ask "soll ich den PR öffnen?" at this point is a rule violation, not
  caution: this gate exists precisely so the sequence completes while I'm
  away. The only two legitimate halts are a blocking finding from `review`
  and a genuinely open scope decision I haven't answered yet.
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
Subagents also never commit: the `issue-implementer` edits the shared working
tree in place and hands its slice back **uncommitted** (it no longer runs in an
isolated worktree, so there is nothing to commit in order to hand work back).
You, the main conversation, commit under the rules above — at the main-issue
resolution gate without asking, otherwise only when I ask for it.

## Worktree Isolation (local sessions)

**This rule applies to local sessions only.** Cloud sessions (Claude Code on
the web, `CLAUDE_CODE_REMOTE=true`) run in their own freshly cloned repository,
which *is* the isolation — there is no shared checkout for one session's edits
to disturb — so they do no worktree work at all: they operate directly on the
`issue/<slug>` branch in that clone. The `worktree_guard.py` hook detects the
remote session — the `CLAUDE_CODE_REMOTE` flag, or any other `CLAUDE_CODE_REMOTE_*`
marker the remote runner sets — and no-ops there (it stays installed so local
sessions of the same repo are still covered). Everything below is about local
sessions.

Every local work session runs in an isolated git worktree, entered at the
**start** of the session — as soon as it's clear the session will touch the
repo, before research or implementation begins, not deferred until the first
edit. Only two things stay in the checkout: a pure investigation/Q&A session
that makes no changes (the "investigate = don't touch files" rule above), and a
trivial change as defined under "Git & Version Control". If a session that began
as investigation turns into work, enter the worktree at that point.

**This rule is enforced, not just documented (locally).** Unlike the branch-name/
co-author rules under "Git & Version Control", whether an edit happened inside
a worktree leaves no trace in the finished commit for a `pre-push` hook to
check afterward — so it kept eroding as unverified guidance. A `PreToolUse`
hook (`worktree_guard.py`, installed by `cloud-session-bootstrap`) now denies
an `Edit`/`Write`/`NotebookEdit` call that would make a non-trivial change
directly in the main checkout, before it happens — in local sessions; in cloud
sessions the same hook no-ops, per the paragraph above. It approximates the
trivial criterion below (it cannot see a diff that hasn't happened yet, so it is
conservative: only a single file with a docs/config extension passes) and
exempts the issue tracker's own directory, since `decompose.md`/`implement.md`
write `issue.md` files directly in the checkout by design. It also
exempts, *during a merge*, exactly the files Git itself reports as conflicted —
so resolving a merge in the main checkout works without disabling the guard;
anything Git does not list as conflicted stays blocked even mid-merge. It does
not see `Bash`-driven file writes — that gap is deliberate, not a sandbox. If
I've explicitly said to work directly in the checkout for a task, touch
`.claude/.worktree-bypass` to disable it for that session — a marker that stays
git-ignored (via `cloud-session-bootstrap`) so a routine `git add -A` cannot
commit it and disable the guard for every checkout.

Once the branch above is selected, code-writing work — direct or delegated —
happens in that worktree, never in the checkout itself:
- **Delegating**: the `issue-implementer` inherits the session's worktree as its
  working directory. It is *not* separately isolated — it edits this same
  worktree in place, one child-issue at a time, and hands each slice back
  **uncommitted**. Because it runs inside a linked worktree, the guard already
  passes and nothing lands in the main checkout.
- **Working directly** (no subagent involved): you are already in the session's
  worktree from the rule above; if not (e.g. the change looked trivial but
  grew), create one now with `git worktree add .worktrees/<slug>` — **no branch
  argument**: git refuses a worktree for the already-checked-out session branch
  (`fatal: ... is already checked out`), so the worktree branches from HEAD onto
  a new helper branch instead, exactly like the `WorktreeCreate` hook does.
  Work and commit there, merge the helper branch back into the session branch
  from the main checkout, then remove worktree and helper branch. Skip all this
  only when the change meets the trivial criterion under "Git & Version Control"
  or I've said to work directly in the current checkout.

**Worktrees live under `.worktrees/`.** Create main-issue worktrees with
`git worktree add .worktrees/<slug>`. Claude Code's native worktree paths
(`EnterWorktree`, `--worktree`, `isolation: worktree`) are safe too: a
`WorktreeCreate` hook (`worktree-create.sh`, installed into every set-up repo by
`cloud-session-bootstrap` alongside the guard) redirects them into
`.worktrees/<name>` instead of the default `.claude/worktrees/`, so every
worktree stays inside this repo's `.worktrees/` convention and its `.gitignore`
entry rather than polluting the main checkout's status. `.worktrees/` is the
only sanctioned location for a main-issue worktree.

Branching from the session's current work is guaranteed by the
`WorktreeCreate` hook itself: it replaces git's native worktree logic entirely
(Claude Code never passes `worktree.baseRef` to it) and always branches from
`HEAD` — whatever you just checked out above. `worktree.baseRef` stays set to
`"head"` in Claude Code's settings as the fallback for a session where the
hook is ever absent; without either, every worktree would silently restart
from `main`, ignoring the branch decided upfront — which is exactly the
branch-awareness problem this section exists to remove from implementation.

**Exception — read-only research/review/test subagents**
(`spec-researcher`, `standards-reviewer`, `spec-reviewer`, `test-runner`): do
**not** isolate these. Their whole job is to judge the actual current state,
uncommitted changes included (`spec-reviewer` diffs against the working tree
by design, `test-runner` runs the suite as it sits on disk) — a worktree only
ever reflects committed history, so isolating them would make them silently
judge a stale snapshot instead of what's really there.

**Worktree layout — one level.** A worktree is a *main-issue*-level thing, and
only locally. Several main-issues can run at the same time — each in its own
worktree under `.worktrees/`, driven by its own independent Claude Code session.
There is no shared orchestrator between those sessions; only the shared `.git`
connects them. `.worktrees/` is listed in `.gitignore` and is never committed.
**Teardown:** a main-issue's worktree lives exactly as long as its pull request.
Once that PR is **merged** — never earlier, since a review may still send
changes back to this worktree — tear it down with
`git worktree remove .worktrees/<slug>` from the main checkout (you cannot
remove the worktree you are standing in). Then sweep any stray worktrees a run
left behind (`git worktree list`, remove the stragglers, `git worktree prune`),
so no worktree outlives the main-issue it belonged to.

There is **no** child-issue worktree level. Within one main-issue's session, its
child-issues are implemented **sequentially, one after another** on the
main-issue branch — not in parallel, and not each in its own worktree. The
`issue-implementer` subagent works them one at a time in the session's own
worktree; there are no throwaway child branches to merge.

Register every worktree flat against the shared `.git` so nesting never
produces `.worktrees/.worktrees/`.

## Delegation to subagents

Keep the main conversation's context for the things that need me in it. Delegate
work whose *output* matters but whose *process* does not — exploration,
implementation, verification — to a subagent, and expect a summary back rather
than files, logs, or diffs.

- **Codebase research** (during `grill-me-for-spec`, or any "how does this work
  today?" question spanning more than a handful of files) → `spec-researcher`.
- **Module-level planning of a decomposed main-issue** (once, after decompose and
  before implement) → `solution-architect`. It writes a temporary `design.md`
  (module map + shared contracts) that the implementers build against; gut-check
  it with `clean-room-review` before implementing. Skip it for a single-slice
  main-issue.
- **Implementing a tracked issue** → `issue-implementer`, one issue at a time.
  Use `tracker.py next` to get the next actionable child-issue and dispatch a
  single implementer for it; when it returns, dispatch the next. Implementers
  run **sequentially, never in parallel** — each edits the session's working
  tree in place on the main-issue branch and hands its slice back.
- **Verification** → the `review` skill, which fans out to `standards-reviewer`,
  `spec-reviewer`, `test-runner`, `docs-reviewer` and, for Axis E,
  `design-reviewer` against the `design.md` plan — or, when no plan exists,
  `clean-room-reviewer` via `clean-room-review`.

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
