#!/usr/bin/env python3
"""Headless runner for behavioral evals.

A behavioral eval checks whether Claude *behaves* as a skill, subagent, or
AGENTS.md rule documents — something no deterministic git check can observe. The
runner chains two synchronous `claude -p` subprocess calls per eval case, the
same headless pattern skill-creator's run_eval.py uses:

  1. Executor: run the scenario `prompt` in an isolated sandbox worktree and
     capture a readable transcript (assistant turns + tool calls).
  2. Grader: run a second `claude -p` with the generalized grader instructions,
     the transcript, and the case's `expectations`, and read back a grading
     object in skill-creator's grading.json shape.

A case passes when its `summary.pass_rate` meets the threshold (default 1.0).
The suite exit status is non-zero if any case fails, so the pre-push hook blocks
the push exactly like a failed deterministic check. `git push --no-verify` is
the sanctioned override.

The runner runs fully against the user's own authenticated `claude` CLI — no API
key, no cloud CI. The subprocess-orchestration and JSON-parsing seams
(run_executor / run_grader / render_transcript / parse_grading) are isolated so
they can be unit-tested with mocked `claude -p` calls.

Eval files are discovered at three colocated locations under the repo root:
  - skills/<name>/evals/evals.json
  - agents/<name>/evals/evals.json
  - evals/agents-md/<rule-slug>/evals.json

Usage:
  run_behavioral_eval.py [--eval-file PATH ...] [--grader-prompt PATH]
                         [--model NAME] [--threshold FLOAT]
                         [--exec-timeout SEC] [--grader-timeout SEC]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

DEFAULT_THRESHOLD = 1.0
DEFAULT_EXEC_TIMEOUT = 600
DEFAULT_GRADER_TIMEOUT = 300
DEFAULT_GRADER_PROMPT = "skills/workflow-evals/agents/grader.md"
EVAL_GLOBS = (
    "skills/*/evals/evals.json",
    "agents/*/evals/evals.json",
    "evals/agents-md/*/evals.json",
)


# --------------------------------------------------------------------------- #
# Discovery and loading                                                       #
# --------------------------------------------------------------------------- #

def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return Path(out)


def discover_eval_files(root: Path) -> list[Path]:
    """All eval files at the three colocated locations, sorted, deduped."""
    found: list[Path] = []
    for pattern in EVAL_GLOBS:
        found.extend(sorted(root.glob(pattern)))
    # Preserve order while removing duplicates.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in found:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def load_evals(path: Path) -> dict:
    return json.loads(Path(path).read_text())


# --------------------------------------------------------------------------- #
# Pure transforms (unit-tested directly)                                       #
# --------------------------------------------------------------------------- #

def render_transcript(stream_lines: list[str]) -> str:
    """Render `claude -p --output-format stream-json` lines to markdown.

    Keeps assistant text, tool calls (name + input), and tool results so the
    grader can judge behavior, not just the final answer. Unparseable lines are
    skipped.
    """
    parts: list[str] = []
    for line in stream_lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = event.get("type")
        if etype == "assistant":
            for item in event.get("message", {}).get("content", []):
                itype = item.get("type")
                if itype == "text" and item.get("text", "").strip():
                    parts.append(f"## Assistant\n\n{item['text'].strip()}")
                elif itype == "tool_use":
                    name = item.get("name", "?")
                    payload = json.dumps(item.get("input", {}), ensure_ascii=False,
                                         indent=2, sort_keys=True)
                    parts.append(f"### Tool call: {name}\n\n```json\n{payload}\n```")
        elif etype == "user":
            for item in event.get("message", {}).get("content", []):
                if item.get("type") == "tool_result":
                    parts.append(f"### Tool result\n\n{_stringify(item.get('content'))}")
    return "\n\n".join(parts)


def _stringify(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(item.get("text", ""))
            else:
                chunks.append(json.dumps(item, ensure_ascii=False))
        return "\n".join(chunks).strip()
    return json.dumps(content, ensure_ascii=False)


def build_grader_prompt(grader_instructions: str, expectations: list[str],
                        transcript: str) -> str:
    """Assemble the grader `claude -p` prompt from parts (pure, testable)."""
    expectations_json = json.dumps(expectations, ensure_ascii=False, indent=2)
    return (
        f"{grader_instructions}\n\n"
        "---\n\n"
        "Grade the transcript below against the expectations. Do NOT write any "
        "files; instead print ONLY the grading JSON object (the schema above) to "
        "stdout, with no prose or code fences around it.\n\n"
        f"## expectations\n\n```json\n{expectations_json}\n```\n\n"
        f"## transcript\n\n{transcript}\n"
    )


def parse_grading(text: str) -> dict:
    """Extract the grading JSON object from grader stdout.

    Tolerates ```json fences and surrounding prose by falling back to the
    outermost brace pair. Raises ValueError if no JSON object is found.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"grader output was not valid JSON: {exc}") from exc
    raise ValueError("grader output contained no JSON object")


def case_passed(result: dict, threshold: float) -> bool:
    """A case passes when it ran without error and met the pass-rate threshold."""
    if result.get("error"):
        return False
    return float(result.get("pass_rate", 0.0)) >= threshold


# --------------------------------------------------------------------------- #
# claude -p invocation (the mock seam)                                         #
# --------------------------------------------------------------------------- #

def _invoke_claude(prompt: str, cwd: Path, model: str | None, timeout: int,
                   stream: bool) -> str:
    cmd = ["claude", "-p", prompt]
    if stream:
        cmd += ["--output-format", "stream-json", "--verbose"]
    if model:
        cmd += ["--model", model]
    # Drop CLAUDECODE so a nested `claude -p` is allowed from inside a session;
    # the guard only exists to prevent interactive-terminal conflicts.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True,
        timeout=timeout, env=env, check=True,
    )
    return result.stdout


def run_executor(prompt: str, workdir: Path, model: str | None,
                 timeout: int) -> str:
    """Run the scenario prompt in the sandbox and return a markdown transcript."""
    out = _invoke_claude(prompt, workdir, model, timeout, stream=True)
    return render_transcript(out.splitlines())


def run_grader(expectations: list[str], transcript: str, grader_instructions: str,
               workdir: Path, model: str | None, timeout: int) -> dict:
    """Run the grader over a transcript and return the parsed grading object."""
    prompt = build_grader_prompt(grader_instructions, expectations, transcript)
    out = _invoke_claude(prompt, workdir, model, timeout, stream=False)
    return parse_grading(out)


# --------------------------------------------------------------------------- #
# Sandbox                                                                      #
# --------------------------------------------------------------------------- #

@contextmanager
def make_sandbox(root: Path):
    """Yield an isolated git worktree of `root`, removed on exit.

    The executor sees the repo's real skills/agents/AGENTS.md but cannot affect
    the working checkout, and any commits it makes vanish with the worktree.
    """
    tmp = Path(tempfile.mkdtemp(prefix="wf-eval-"))
    worktree = tmp / "wt"
    try:
        subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", "-q",
             str(worktree)],
            check=True, capture_output=True, text=True,
        )
        yield worktree
    finally:
        subprocess.run(
            ["git", "-C", str(root), "worktree", "remove", "--force",
             str(worktree)],
            check=False, capture_output=True, text=True,
        )
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Orchestration                                                                #
# --------------------------------------------------------------------------- #

def _error_result(case_id, message: str) -> dict:
    return {"id": case_id, "pass_rate": 0.0, "grading": None, "error": message}


def run_case(case: dict, grader_instructions: str, workdir: Path,
             model: str | None, exec_timeout: int, grader_timeout: int) -> dict:
    """Execute then grade one eval case in an already-prepared sandbox."""
    case_id = case.get("id")
    try:
        transcript = run_executor(case["prompt"], workdir, model, exec_timeout)
    except (subprocess.SubprocessError, OSError) as exc:
        return _error_result(case_id, f"executor failed: {exc}")
    try:
        grading = run_grader(case.get("expectations", []), transcript,
                             grader_instructions, workdir, model, grader_timeout)
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        return _error_result(case_id, f"grader failed: {exc}")
    pass_rate = float(grading.get("summary", {}).get("pass_rate", 0.0))
    return {"id": case_id, "pass_rate": pass_rate, "grading": grading,
            "error": None}


def run_suite(eval_files: list[Path], grader_instructions: str, root: Path,
              model: str | None, exec_timeout: int, grader_timeout: int,
              threshold: float) -> list[dict]:
    """Run every case of every eval file, each in its own sandbox."""
    file_results: list[dict] = []
    for path in eval_files:
        data = load_evals(path)
        source = data.get("skill_name") or data.get("agent_name") \
            or data.get("rule_id") or str(path)
        cases: list[dict] = []
        for case in data.get("evals", []):
            with make_sandbox(root) as workdir:
                result = run_case(case, grader_instructions, workdir, model,
                                  exec_timeout, grader_timeout)
            result["passed"] = case_passed(result, threshold)
            cases.append(result)
        file_results.append({"source": source, "path": str(path),
                             "cases": cases})
    return file_results


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def _print_report(file_results: list[dict]) -> tuple[int, int]:
    passed = failed = 0
    for fr in file_results:
        print(f"\n{fr['source']}  ({fr['path']})", file=sys.stderr)
        for case in fr["cases"]:
            ok = case["passed"]
            passed += ok
            failed += not ok
            status = "PASS" if ok else "FAIL"
            detail = case["error"] or f"pass_rate={case['pass_rate']:.2f}"
            print(f"  [{status}] case {case['id']}: {detail}", file=sys.stderr)
    return passed, failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-file", action="append", default=None,
                        help="Eval file(s) to run; defaults to discovery.")
    parser.add_argument("--grader-prompt", default=DEFAULT_GRADER_PROMPT,
                        help="Path to the grader instructions markdown.")
    parser.add_argument("--model", default=None)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--exec-timeout", type=int, default=DEFAULT_EXEC_TIMEOUT)
    parser.add_argument("--grader-timeout", type=int,
                        default=DEFAULT_GRADER_TIMEOUT)
    args = parser.parse_args(argv)

    root = repo_root()
    if args.eval_file:
        eval_files = [Path(p) for p in args.eval_file]
    else:
        eval_files = discover_eval_files(root)

    if not eval_files:
        print("No eval files found; nothing to run.", file=sys.stderr)
        return 0

    grader_path = (root / args.grader_prompt) if not Path(args.grader_prompt).is_absolute() \
        else Path(args.grader_prompt)
    if not grader_path.exists():
        print(f"Grader prompt not found: {grader_path}", file=sys.stderr)
        return 2
    grader_instructions = grader_path.read_text()

    file_results = run_suite(eval_files, grader_instructions, root, args.model,
                             args.exec_timeout, args.grader_timeout,
                             args.threshold)
    passed, failed = _print_report(file_results)
    print(f"\nBehavioral evals: {passed} passed, {failed} failed", file=sys.stderr)
    if failed:
        print("Bypass with `git push --no-verify` if this is deliberate.",
              file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
