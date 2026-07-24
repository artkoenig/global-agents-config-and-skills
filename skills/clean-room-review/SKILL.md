---
name: clean-room-review
description: Get an independent, unbiased solution proposal for a problem from an external expert (the `clean-room-reviewer` subagent) who has never seen your code, your docs, or the answer you are leaning toward — then reconcile that fresh proposal with the real domain and codebase. Use it when you want a genuine second opinion that is not anchored to the status quo: a design decision, an architecture choice, a "are we overcomplicating this?" gut-check. Not for reviewing existing code line-by-line (that is `standards-reviewer`); the reviewer never sees the diff or the existing solution. The `review` skill's Clean-Room axis (Axis E) is built on this workflow — it feeds the reviewer the problem and the raw data, then reconciles the blind proposal against the implementation.
user-invocable: true
---

# Clean-Room Review

Get a solution proposal from an expert who works in a **clean room**: they never
see the existing code, the documentation, or the solution you already have in
mind. Because their proposal is uncontaminated by the status quo, it tells you
what someone would build if they started today — which is exactly the signal you
lose once you are deep in your own implementation.

The main conversation stays the only party that knows the real code and domain.
The reviewer designs blind; you translate their blind proposal back into reality.

## When to use

- A design or architecture decision where you suspect the status quo (or your own
  first instinct) is biasing you.
- A "how would someone else do this?" or "are we overcomplicating this?" check.
- Any point where an independent proposal, grounded in nothing but the stated
  requirements, is more valuable than a critique of what already exists.

Do **not** use it to review existing code (`standards-reviewer`), to check a
diff against a spec line-by-line (`spec-reviewer`), or to research how the
current system works (`spec-researcher`). The reviewer itself never sees the
diff. Turning its blind proposal into a verdict on an existing implementation is
the caller's job — the `review` skill's Clean-Room axis (Axis E) does exactly
that, and is the one sanctioned way to point this workflow at a diff.

## The one rule that makes this work: neutrality

The entire value collapses if the reviewer is biased by the status quo or by your
opinion. Two disciplines enforce that, and they are non-negotiable:

1. **The brief carries no solution and no status quo.** When you frame the
   problem for the reviewer, describe the goal and the hard constraints only.
   Do **not** describe the current implementation, do **not** propose an
   approach, do **not** hint at the answer you prefer. Give the **raw data and
   its shape** (tree, SQL database, graph, files, …) as the factual substrate the
   reviewer designs on, but withhold **derived** domain data and domain logic —
   the reviewer should form its own domain model, so that ours is what gets
   challenged rather than silently assumed. (Answering it later — see rule 2 — is
   different: once the reviewer *asks*, you may share domain knowledge plainly.)
2. **You answer their questions with status-quo facts only — never steering.**
   When the reviewer asks something, answer from the actual domain and code as it
   is, plainly and neutrally. Reflect *what is*, never *what you'd like them to
   conclude*. No leading answers, no "we usually do X", no nudging toward your
   own solution.

## Workflow

### 1. Frame the question and derive the role
From the problem's domain, decide what expert should answer it and state it as a
role — "software architect", "backend developer", "UX designer", "data
engineer", etc. Then write a **neutral brief**: the goal to achieve and the hard
constraints around it, with no proposed solution and no description of the
current implementation (see neutrality rule 1).

### 2. Spawn the clean-room reviewer
Spawn the `clean-room-reviewer` subagent, passing it the **role** and the
**problem** brief. It has no access to this repository by design — that is the
clean room. Its definition is the single source of truth for how it behaves;
just pass the two inputs.

### 3. Run the question/answer loop
The reviewer cannot talk to you mid-run (no subagent can — see AGENTS.md
"Delegation to subagents"), so the loop is externalized here:

- The reviewer responds in one of two modes: a batch of **clarifying questions**,
  or its **solution proposal**.
- If it returns questions, answer each one from the real code and domain —
  **status quo only, no steering** (neutrality rule 2). Consult the codebase (or
  a `spec-researcher` briefing) as needed to answer accurately.
- Continue the **same** reviewer with those answers (via `SendMessage`, so its
  context is intact — do not spawn a fresh one and lose the thread).
- Repeat until the reviewer delivers a proposal. Keep it converging; if it has
  not proposed after ~3 rounds, ask it to proceed on stated assumptions.

Record **every** question/answer pair in a table in the main conversation as you
go, so the reasoning is visible and auditable:

| # | Reviewer's question | Answer (status quo) |
| --- | --- | --- |
| 1 | … | … |
| 2 | … | … |

### 4. Receive the independent proposal
The reviewer returns its "how I would do it" proposal — approach, key decisions,
trade-offs, risks, alternatives. This is the clean-room artifact: what an expert
would build from the requirements alone.

### 5. Synthesize against reality
Now put back what the reviewer never had. Using the **actual domain knowledge and
code**, turn their blind proposal into a concrete recommendation for the user:

- Where the clean-room proposal **agrees** with the current approach — that is
  independent confirmation the status quo is sound.
- Where it **improves** on the status quo — a change worth making.
- Where it is **impractical** against real constraints the reviewer could not see
  — say so, with the specific constraint that rules it out.

Present the final proposal short, plain, and concrete (per AGENTS.md), and keep
the Q&A table with it so the user can trace how the reviewer got there.

## The subagent

`clean-room-reviewer` is defined in `agents/` at the repository root of
[global-agents-config-and-skills](https://github.com/artkoenig/global-agents-config-and-skills),
loaded into `~/.claude/agents/` by the `cloud-session-bootstrap` SessionStart
hook. It runs on `opus` with only `WebSearch`/`WebFetch` — no file tools — so it
literally cannot inspect this repository. If it is unavailable in the current
environment, say so rather than role-playing the reviewer yourself in the main
conversation: a reviewer that can see the code is not a clean room.
