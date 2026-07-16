---
name: workflow-evals
description: The self-testing apparatus for this repo's own workflow rules — the deterministic git-workflow checks and the behavioral evals that verify skills, subagents, and AGENTS.md rules actually behave as documented. Use it to run the checks/evals, to author a new eval when a rule/skill/subagent changes, or to understand how the pre-push gate is wired. Trigger on phrases like "run the workflow evals", "check the git rules", "add an eval for this rule", "why did my push get blocked", "test that the skill triggers", or "the pre-push hook".
user-invocable: true
---

# Workflow Evals

This repo's `AGENTS.md`, skills, and subagents govern how Claude Code works. This
skill is how those rules are kept honest: every rule is bound to a test, and the
tests run automatically before every push. Two test styles cover two kinds of
rule.

| Style | For rules that are… | Implemented as | Speed |
| :--- | :--- | :--- | :--- |
| **Deterministic checks** | fully readable from the finished git state | pure Python + `unittest`, no LLM | instant |
| **Behavioral evals** | only instructions to the LLM's behavior | headless `claude -p` runs graded by an LLM judge | slow |

Both hang off one versioned `pre-push` hook and are also runnable by hand. A
failure blocks the push hard; `git push --no-verify` is the sanctioned override.

## Deterministic checks

`scripts/git_workflow_rules.py` holds four pure predicates and a thin CLI over
them. The predicates (unit-tested in `scripts/test_git_workflow_rules.py`):

- `is_valid_branch_name(name)` — branch matches `^issue/[a-z0-9-]+$` (rule 7).
- `is_protected_ref(ref)` — ref is a protected branch (`main`/`master`) that must
  never receive a push (rule 8).
- `commit_has_agent_coauthor(message)` — message carries any `Co-authored-by`
  trailer (rule 9; no allow-list).
- `is_trivial_change(files, added_lines)` — the deterministic trivial criterion
  (exactly one file AND (≤1 added line OR a `.md`/`.json`/`.yaml`/`.yml`/`.txt`
  extension)). Not a push gate — it informs the issue-tracking decision.

**Run at push time:** installed via `core.hooksPath=.githooks`; the
`.githooks/pre-push` hook forwards git's push lines to
`git_workflow_rules.py pre-push`. Installed in every repo by the
`cloud-session-bootstrap` skill.

**Run manually:** `python3 scripts/git_workflow_rules.py check` validates the
current checkout (branch name, not on a protected branch, no co-author trailers
in local commits). Exit 0 = clean, 1 = violations.

## Behavioral evals

`scripts/run_behavioral_eval.py` chains two synchronous `claude -p` calls per
eval case — a headless pattern, because the in-session Agent/Task tool can't be
called from a shell hook:

1. **Executor** runs the scenario `prompt` in an isolated sandbox worktree and a
   markdown transcript (assistant turns + tool calls) is captured.
2. **Grader** runs `agents/grader.md` over that transcript and the case's
   `expectations`, returning a grading object.

A case passes when `summary.pass_rate` meets the threshold (default `1.0`). The
suite exits non-zero if any case fails, so the pre-push gate treats a failed eval
exactly like a failed deterministic check. Everything runs against your own
authenticated `claude` CLI login — no API key, no cloud CI. Each case runs in its
own throwaway git worktree, so the executor cannot touch the real checkout.

**Run:** `python3 scripts/run_behavioral_eval.py` (discovers every eval file) or
`--eval-file <path>` for one. The full suite runs on every push, regardless of
which files changed.

### Where evals live (colocated)

One `evals.json` format, one runner, three locations — the identifying top-level
key varies by location:

| Under test | Path | Top-level key |
| :--- | :--- | :--- |
| Skill | `skills/<name>/evals/evals.json` | `skill_name` |
| Subagent | `agents/<name>/evals/evals.json` | `agent_name` |
| AGENTS.md rule | `evals/agents-md/<rule-slug>/evals.json` | `rule_id` |

`evals.json` shape (compatible with skill-creator's schema):

```json
{
  "skill_name": "issue-tracker",
  "evals": [
    {
      "id": 1,
      "prompt": "Scenario the executor runs",
      "expected_output": "Human-readable description of success",
      "expectations": ["A verifiable statement about the behavior", "..."]
    }
  ]
}
```

`grading.json` shape is defined in `agents/grader.md`.

## Authoring an eval

Whenever a rule, skill, or subagent changes, draft the matching eval cases
(scenario `prompt` + prose `expectations`) and present them for review. Only
after the maintainer approves are they committed and become part of the suite.
Aim expectations at *discriminating* behavior — assertions that pass only when
the work is genuinely done right, not when a wrong output would also satisfy
them.

## Scope note

The deterministic checks run in every repo (via `cloud-session-bootstrap`); the
behavioral evals only ever exist in this config repo, so the eval step is a
no-op everywhere else — no "is this the config repo?" logic is needed.
