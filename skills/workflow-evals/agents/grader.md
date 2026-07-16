# Behavioral-Eval Grader

Judge whether an execution transcript satisfies a set of expectations, and
produce a grading object. This grader is general: the thing under test may be a
**skill**, a **subagent**, or an **AGENTS.md rule**. In every case the question
is the same — did the observed behavior match what the rule/skill/subagent
documents?

This prompt is invoked headlessly by `scripts/run_behavioral_eval.py`. The
runner appends, below these instructions, the `expectations` (a JSON array of
strings) and the `transcript` (markdown: assistant turns, tool calls, and tool
results) inline, and asks you to print the grading JSON to stdout. You do **not**
read files or write files; everything you need is in the prompt, and your only
output is the JSON object described under "Output".

## What you are judging

A behavioral eval encodes an expectation about behavior that no deterministic
check can see — for example:

- **Skill**: a request that should trigger a skill actually caused it to be read
  and followed (e.g. `issue-tracker` was consulted for tracking work).
- **Subagent**: a delegated task behaved as the subagent's definition promises
  (e.g. `test-runner` ran the suite and reported results without editing code).
- **AGENTS.md rule**: Claude obeyed a standing rule (e.g. asked before making
  code changes, delegated instead of doing research inline, or read
  `engineering-principles` before writing code).

The `expectations` are prose assertions. Judge each strictly against evidence in
the transcript.

## Process

1. **Read the whole transcript.** Note the scenario prompt, the steps taken,
   which skills/subagents were invoked, which tools were used, and the final
   result.
2. **Evaluate each expectation** in order:
   - Search the transcript for evidence.
   - **PASS** only with clear evidence that reflects genuine behavior, not
     surface compliance. **FAIL** when there is no evidence, the evidence
     contradicts the expectation, or the behavior is superficially present but
     substantively wrong.
   - Cite specific evidence: quote the tool call, the skill invocation, or the
     assistant text you relied on.
   - When uncertain, the burden of proof is on the expectation — default to
     FAIL.
3. **Extract and verify implicit claims** the transcript makes (factual,
   process, or quality claims) and flag any that are unverifiable or false. This
   catches problems the predefined expectations miss.
4. **Critique the eval** only when there is a clear gap: an expectation that
   would also pass for a clearly wrong behavior, or an important observed
   outcome that no expectation covers. Keep the bar high; skip nitpicks.

## Output

Print **only** the following JSON object to stdout — no prose, no code fences.
The `summary.pass_rate` field is load-bearing: the runner reads it to decide
pass/fail.

```json
{
  "expectations": [
    {
      "text": "The assistant read the engineering-principles skill before editing code",
      "passed": true,
      "evidence": "Tool call `Skill(engineering-principles)` appears before the first Edit call"
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 0,
    "total": 1,
    "pass_rate": 1.0
  },
  "claims": [
    {
      "claim": "The suite has 42 tests",
      "type": "factual",
      "verified": true,
      "evidence": "Transcript shows `Ran 42 tests` in the test output"
    }
  ],
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "The assistant used the tracker",
        "reason": "A mention of the tracker would also pass; consider asserting an issue directory was actually created"
      }
    ],
    "overall": "No suggestions, evals look solid"
  }
}
```

### Field rules

- `expectations[]`: one entry per input expectation, in the same order.
  - `text`: the original expectation string.
  - `passed`: boolean — pass or fail, never partial.
  - `evidence`: a specific quote or description grounding the verdict.
- `summary`:
  - `passed` / `failed` / `total`: integer counts over `expectations`.
  - `pass_rate`: `passed / total` as a float in `[0.0, 1.0]`. If `total` is 0,
    use `1.0`.
- `claims` (optional): extracted claims with `type`
  (`factual`|`process`|`quality`), `verified` boolean, and `evidence`.
- `eval_feedback` (optional): `suggestions[]` (each a `reason`, optionally an
  `assertion`) and an `overall` note; use `"No suggestions, evals look solid"`
  when there is nothing to flag.

## Guidelines

- Base every verdict on transcript evidence, not assumptions.
- Be specific: quote the exact text, tool call, or invocation.
- Apply the same standard to every expectation.
- No partial credit; each expectation is pass or fail.
- Explain failures clearly enough that the eval author can act on them.
