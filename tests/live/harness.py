#!/usr/bin/env python3
"""Headless live check of fmt against real Claude replies.

For each checked mode it runs three kinds of prompt through `claude -p` with
the plugin loaded, and grades every final reply with an independent judge
(tests/live/common.py) as well as the plugin's own checker:

  natural      the mode is set and injected; the question is one the mode is
               not the obvious shape for. Pass: the final reply has the shape.
  adversarial  as natural, but the prompt asks for two paragraphs of prose.
               Reported, not gated: Claude may deliberately honor a format the
               message asks for over the standing mode. The invariants (at most
               two replies, the retry guard) still gate.
  forced miss  injection switched off (CLAUDE_FMT_NO_INJECT=1, synthetic), so
               the reply misses and the Stop hook must rescue it. Pass: exactly
               two replies, the first failing the check and the second passing
               it and the judge.

Plus `original`: exactly one reply, and the decision trace shows neither hook
produced output, with a positive control showing the same trace records
injection when a mode is set.

Every run must have at most two assistant replies. The judge is calibrated
first against known-good and known-bad corpus replies; a misgrade aborts.

Usage: python3 tests/live/harness.py [--model sonnet] [--opus-modes tabular,flow]
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

QUESTIONS = {
    "concise": "Tell me the full history of the HTTP protocol, from HTTP/0.9 to HTTP/3, in detail, with examples of what changed in each version.",
    "bulleted": "Tell me the story of how the Unix operating system came to be.",
    "tabular": "Walk me through setting up SSH key authentication on a new Linux server.",
    "flow": "Compare REST and GraphQL for designing a public API.",
    "block": "Compare git merge and git rebase.",
}
PROSE = " Answer in two paragraphs of prose, with no tables, lists or diagrams."
LONG = " Write at least 400 words."


def run_case(name, mode, prompt, model, no_inject, workdir):
    state = os.path.join(workdir, "state-%s.json" % name)
    trace = os.path.join(workdir, "trace-%s.jsonl" % name)
    cli = os.path.join(common.ROOT, "bin", "claude-fmt")
    subprocess.run([sys.executable, cli, "mode", mode], env=dict(os.environ, CLAUDE_FMT_STATE=state),
                   check=True, capture_output=True)
    env = {"CLAUDE_FMT_STATE": state, "CLAUDE_FMT_TRACE": trace}
    if no_inject:
        env["CLAUDE_FMT_NO_INJECT"] = "1"
    texts, events = common.run_claude(prompt, model, env_extra=env)
    return {"name": name, "mode": mode, "model": model, "prompt": prompt, "texts": texts,
            "trace": common.read_trace(trace), "events_seen": len(events)}


def grade(case, kind):
    mode, texts = case["mode"], case["texts"]
    case["kind"] = kind
    case["checks"] = [list(common.check(mode, t)) if mode in common.fmt_check.CHECKED_MODES else None for t in texts]
    problems = []
    if not texts:
        problems.append("no reply")
    if len(texts) > 2:
        problems.append("%d replies (at most 2 allowed)" % len(texts))
    if kind == "original":
        if len(texts) != 1:
            problems.append("original produced %d replies" % len(texts))
        produced = [r for r in case["trace"] if r.get("output")]
        if produced:
            problems.append("original: a hook produced output: %s" % produced)
        if not any(r.get("handler") == "inject" for r in case["trace"]):
            problems.append("original: no inject decision traced (trace not working?)")
    elif texts:
        final = texts[-1]
        stops = [(r.get("retry"), r.get("output")) for r in case["trace"] if r.get("handler") == "stop"]
        case["stops"] = stops
        if len(texts) == 2 and stops != [(False, True), (True, False)]:
            problems.append("two replies but Stop trace %s, expected [send-back, silent retry]" % stops)
        ok, reason = common.check(mode, final)
        verdict, evidence = common.judge(mode, final)
        case["judge"] = {"verdict": verdict, "evidence": evidence}
        if not ok:
            problems.append("final reply fails the checker: %s" % reason)
        if verdict != "YES":
            problems.append("judge %s: %s" % (verdict, evidence))
        if kind == "forced_miss":
            if len(texts) != 2:
                problems.append("forced miss produced %d replies, expected 2" % len(texts))
            elif common.check(mode, texts[0])[0]:
                problems.append("forced miss: first reply already passed, so nothing was rescued")
            # The retry guard, observed directly: one send-back, then the
            # continuation's Stop is marked as a retry and produces nothing.
            if stops != [(False, True), (True, False)]:
                problems.append("forced miss: Stop trace %s, expected [send-back, silent retry]" % stops)
        if kind == "natural" and not any(r.get("handler") == "inject" and r.get("output") for r in case["trace"]):
            problems.append("positive control: no injection traced for a set mode")
    # An adversarial prompt asks for a different format in the same message.
    # Claude may deliberately honor the message over the standing mode, which
    # is a product question, not a plugin defect: report the shape outcome
    # without gating on it. The invariants (at most two replies, the retry
    # guard) still gate.
    case["notes"] = []
    if kind == "adversarial":
        shape = [p for p in problems if p.startswith(("final reply fails", "judge "))]
        case["notes"] = shape
        case["in_shape"] = not shape
        case["rescued"] = not shape and len(texts) == 2
        problems = [p for p in problems if p not in shape]
    case["problems"] = problems
    case["pass"] = not problems
    return case


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--opus-modes", default="tabular,flow")
    parser.add_argument("--jobs", type=int, default=5)
    args = parser.parse_args()

    out = common.results_dir("harness")
    try:
        return run(args, out)
    finally:
        common.cleanup_run_dir()


def run(args, out):
    work = common.run_dir()
    modes = list(QUESTIONS)

    print("calibrating judge (%s) ..." % common.JUDGE_MODEL, flush=True)
    misgrades = common.calibrate_judge(modes)
    common.write_json(os.path.join(out, "judge-calibration.json"), misgrades)
    if misgrades:
        print("ABORT: judge misgraded known fixtures: %s" % json.dumps(misgrades, indent=2))
        return 2

    plan = []
    for mode in modes:
        q = QUESTIONS[mode]
        plan.append(("natural-%s-%s" % (mode, args.model), mode, q, args.model, False, "natural"))
        prose = q + (LONG if mode == "concise" else PROSE)
        plan.append(("adversarial-%s" % mode, mode, prose, args.model, False, "adversarial"))
        plan.append(("forced-miss-%s" % mode, mode, prose, args.model, True, "forced_miss"))
    for mode in [m for m in args.opus_modes.split(",") if m]:
        plan.append(("natural-%s-opus" % mode, mode, QUESTIONS[mode], "opus", False, "natural"))
    plan.append(("original", "original", QUESTIONS["tabular"], args.model, False, "original"))

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run_case, n, m, p, mdl, ni, work): kind for n, m, p, mdl, ni, kind in plan}
        for future in concurrent.futures.as_completed(futures):
            case = grade(future.result(), futures[future])
            results.append(case)
            print("%-4s %-28s replies=%d %s%s" % ("PASS" if case["pass"] else "FAIL", case["name"],
                                                 len(case["texts"]), "; ".join(case["problems"]),
                                                 ("  [reported: %s]" % "; ".join(case["notes"])) if case["notes"] else ""), flush=True)

    results.sort(key=lambda c: c["name"])
    common.write_json(os.path.join(out, "results.json"), results)
    passed = sum(c["pass"] for c in results)
    adversarial = [c for c in results if c["kind"] == "adversarial"]
    print("\n%d/%d cases passed. Adversarial (reported, not gated): %d/%d in shape, %d rescued by the "
          "send-back. Details: %s" % (passed, len(results), sum(c["in_shape"] for c in adversarial),
                                      len(adversarial), sum(c["rescued"] for c in adversarial), out))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
