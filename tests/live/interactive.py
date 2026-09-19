#!/usr/bin/env python3
"""Scripted interactive Claude Code sessions (via tmux) proving the done-oracle end to end.

  1  install: marketplace added with the CLI at local scope, plugin installed
     through the in-session /plugin menu choosing local scope, so only the
     scratch project's .claude/settings.local.json changes
  2  in a fresh session, /fmt:mode <m> then a question, for every checked
     mode: the final reply passes the checker and an independent judge
  3  forced miss (a session with CLAUDE_FMT_NO_INJECT=1): exactly two
     replies, the second rescuing the first, and "Stop hook feedback" on screen
  4  /fmt:mode original: one reply, and the decision trace shows no hook
     produced output; then persistence: a mode set before /exit is in force in
     a brand-new session, through the real default state path
     ($XDG_CONFIG_HOME/claude-fmt/state.json, no CLAUDE_FMT_STATE override)

The session transcript is the ground truth for reply text; the screen is
checked for what the user sees. The caller's ~/.claude/settings.json and
~/.config/claude-fmt/state.json are fingerprinted before and after every step,
and cleanup always runs.

Usage: python3 tests/live/interactive.py [--source <path-or-owner/repo>] [--model sonnet]
"""

import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from harness import QUESTIONS, PROSE  # noqa: E402

HOME = os.path.expanduser("~")
GLOBAL_SETTINGS = os.path.join(HOME, ".claude", "settings.json")
REAL_STATE = os.path.join(HOME, ".config", "claude-fmt", "state.json")
SESSION = "claude-fmt-live-%d" % os.getpid()
PLUGIN_FILES = [
    os.path.join(HOME, ".claude", "plugins", "known_marketplaces.json"),
    os.path.join(HOME, ".claude", "plugins", "installed_plugins.json"),
]
TURN_TIMEOUT = 240
STABLE_SECONDS = 8


class Flake(Exception):
    """A mechanical failure driving the terminal, as opposed to an oracle failure."""


def claude_fmt_traces():
    """Everything outside the scratch project that would mention claude-fmt if it were installed."""
    found = []
    for path in PLUGIN_FILES:
        try:
            with open(path, encoding="utf-8") as f:
                if "claude-fmt" in f.read():
                    found.append(path)
        except OSError:
            pass
    found += glob.glob(os.path.join(HOME, ".claude", "plugins", "cache", "claude-fmt"))
    found += glob.glob(os.path.join(HOME, ".claude", "plugins", "data", "fmt-claude-fmt*"))
    return found


def fingerprint(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def tmux(*args, check=False):
    return subprocess.run(["tmux"] + list(args), capture_output=True, text=True, check=check)


def pane():
    return tmux("capture-pane", "-p", "-J", "-t", SESSION, "-S", "-200").stdout


def send_text(text):
    tmux("send-keys", "-t", SESSION, "-l", text)
    time.sleep(0.4)
    tmux("send-keys", "-t", SESSION, "Enter")


def wait_for(predicate, timeout, what):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(1)
    raise Flake("timed out waiting for %s" % what)


class Scratch(object):
    def __init__(self, source, model):
        self.source = source
        self.model = model
        self.dir = os.path.realpath(tempfile.mkdtemp(prefix="fmt-interactive-"))
        self.xdg = os.path.join(self.dir, "xdg")
        self.trace = os.path.join(self.dir, "trace.jsonl")
        subprocess.run(["git", "init", "-q", self.dir], check=True)
        self.guard = {GLOBAL_SETTINGS: fingerprint(GLOBAL_SETTINGS), REAL_STATE: fingerprint(REAL_STATE)}

    def assert_untouched(self, step):
        for path, before in self.guard.items():
            if fingerprint(path) != before:
                raise RuntimeError("%s changed during %s" % (path, step))

    def cli(self, *args):
        return subprocess.run(["claude", "plugin"] + list(args), cwd=self.dir, capture_output=True, text=True)

    def env(self, no_inject=False):
        env = ["XDG_CONFIG_HOME=%s" % self.xdg, "CLAUDE_FMT_TRACE=%s" % self.trace]
        if no_inject:
            env.append("CLAUDE_FMT_NO_INJECT=1")
        return env

    def start(self, no_inject=False):
        tmux("kill-session", "-t", SESSION)
        command = "env -u CLAUDE_FMT_STATE %s claude --model %s --strict-mcp-config --setting-sources project,local --tools ''" % (
            " ".join(self.env(no_inject)), self.model)
        tmux("new-session", "-d", "-s", SESSION, "-x", "200", "-y", "50", "-c", self.dir, command, check=True)
        self.started = time.time()
        wait_for(lambda: "trust" in pane().lower() or "❯" in pane(), 30, "the session to start")
        if "trust this folder" in pane().lower():
            tmux("send-keys", "-t", SESSION, "Down")
            time.sleep(0.5)
            tmux("send-keys", "-t", SESSION, "Enter")
        wait_for(lambda: "❯" in pane() and "trust" not in pane().lower(), 30, "the prompt")
        time.sleep(2)

    def stop(self):
        send_text("/exit")
        time.sleep(3)
        tmux("kill-session", "-t", SESSION)

    def transcript(self):
        paths = [
            path for path in glob.glob(os.path.join(common.transcript_dir(self.dir), "*.jsonl"))
            if os.path.getmtime(path) >= self.started - 5
        ]
        if not paths:
            return []
        newest = max(paths, key=os.path.getmtime)
        events = []
        with open(newest, encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except ValueError:
                    pass
        return common.assistant_texts(events)

    def mode(self, arg, expect):
        seen = pane().count(expect)
        send_text("/fmt:mode %s" % arg if arg else "/fmt:mode")
        wait_for(lambda: pane().count(expect) > seen, 30, "a new '%s' on screen" % expect)

    def ask(self, prompt):
        """Send a prompt; return the assistant texts that answered it."""
        before = len(self.transcript())
        send_text(prompt)
        wait_for(lambda: len(self.transcript()) > before, TURN_TIMEOUT, "a reply in the transcript")
        last, since = None, time.time()
        deadline = time.time() + TURN_TIMEOUT
        while time.time() < deadline:
            screen = pane()
            snapshot = (len(self.transcript()), screen)
            busy = "esc to interrupt" in screen.lower()
            if snapshot != last or busy:
                last, since = snapshot, time.time()
            elif time.time() - since >= STABLE_SECONDS:
                return self.transcript()[before:]
            time.sleep(1)
        raise Flake("turn did not settle")

    def install(self):
        added = self.cli("marketplace", "add", self.source, "--scope", "local")
        if added.returncode != 0:
            raise RuntimeError("marketplace add failed: %s" % added.stderr[-300:])
        self.assert_untouched("marketplace add")
        via = "tui"
        self.start()
        send_text("/plugin install fmt@claude-fmt")
        try:
            wait_for(lambda: "local scope" in pane(), 30, "the install menu")
            for _ in range(5):
                chosen = [l for l in pane().splitlines() if "local scope" in l]
                if chosen and chosen[-1].lstrip().startswith(">"):
                    break
                tmux("send-keys", "-t", SESSION, "Down")
                time.sleep(0.5)
            else:
                raise Flake("could not select local scope")
            tmux("send-keys", "-t", SESSION, "Enter")
            wait_for(lambda: self.enabled(), 60, "the plugin to be enabled in settings.local.json")
        except Flake:
            via = "cli"
            tmux("send-keys", "-t", SESSION, "Escape")
            installed = self.cli("install", "fmt@claude-fmt", "--scope", "local")
            if installed.returncode != 0:
                raise RuntimeError("install failed: %s" % installed.stderr[-300:])
        finally:
            for _ in range(3):
                tmux("send-keys", "-t", SESSION, "Escape")
                time.sleep(0.3)
            self.stop()
        self.assert_untouched("install")
        return via

    def enabled(self):
        path = os.path.join(self.dir, ".claude", "settings.local.json")
        try:
            with open(path, encoding="utf-8") as f:
                return bool(json.load(f).get("enabledPlugins", {}).get("fmt@claude-fmt"))
        except (OSError, ValueError):
            return False

    def cleanup(self):
        tmux("kill-session", "-t", SESSION)
        self.cli("uninstall", "fmt@claude-fmt", "--scope", "local")
        self.cli("marketplace", "remove", "claude-fmt", "--scope", "local")
        shutil.rmtree(common.transcript_dir(self.dir), ignore_errors=True)
        for path in glob.glob(os.path.join(HOME, ".claude", "plugins", "cache", "claude-fmt")) + glob.glob(
            os.path.join(HOME, ".claude", "plugins", "data", "fmt-claude-fmt*")
        ):
            shutil.rmtree(path, ignore_errors=True)
        shutil.rmtree(self.dir, ignore_errors=True)


def graded(mode, texts, kind):
    final = texts[-1] if texts else ""
    ok, reason = common.check(mode, final) if final else (False, "no reply")
    verdict, evidence = common.judge(mode, final) if final else ("ERROR", "no reply")
    problems = []
    if not texts:
        problems.append("no reply")
    if len(texts) > 2:
        problems.append("%d replies (at most 2)" % len(texts))
    if not ok:
        problems.append("checker: %s" % reason)
    if verdict != "YES":
        problems.append("judge %s: %s" % (verdict, evidence))
    return {"kind": kind, "mode": mode, "replies": len(texts), "texts": texts, "check": [ok, reason],
            "judge": [verdict, evidence], "problems": problems, "pass": not problems}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=common.ROOT, help="marketplace source: a local path or owner/repo")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--skip-calibration", action="store_true")
    args = parser.parse_args()
    if not shutil.which("tmux"):
        print("tmux is required")
        return 2

    if os.environ.get("CLAUDE_CONFIG_DIR"):
        print("CLAUDE_CONFIG_DIR is set; this script checks the default config location only")
        return 2
    existing = claude_fmt_traces()
    if existing:
        print("claude-fmt is already registered or installed here (%s). Uninstall it first: this "
              "script installs and removes its own copy and must not touch yours." % ", ".join(existing))
        return 2

    out = common.results_dir("interactive")
    if not args.skip_calibration:
        misgrades = common.calibrate_judge(list(QUESTIONS))
        if misgrades:
            print("ABORT: judge misgraded known fixtures: %s" % misgrades)
            return 2

    scratch = Scratch(args.source, args.model)
    results, flakes = [], []
    try:
        via = scratch.install()
        problems = [] if scratch.enabled() else ["plugin not enabled"]
        if via != "tui":
            problems.append("the /plugin menu could not be driven; installed with the CLI instead")
        results.append({"kind": "install", "source": args.source, "via": via, "pass": not problems,
                        "problems": problems})
        print("install via %s: %s" % (via, "PASS" if scratch.enabled() else "FAIL"), flush=True)

        # Oracle 2: every checked mode in one fresh session.
        scratch.start()
        for mode in ("concise", "bulleted", "tabular", "flow", "block"):
            scratch.mode(mode, "mode → %s" % mode)
            result = graded(mode, scratch.ask(QUESTIONS[mode]), "session")
            results.append(result)
            print("%-4s session %-8s replies=%d %s" % ("PASS" if result["pass"] else "FAIL", mode,
                                                     result["replies"], "; ".join(result["problems"])), flush=True)

        # Oracle 4a: original leaves the reply untouched.
        scratch.mode("original", "mode → original")
        mark = len(common.read_trace(scratch.trace))
        texts = scratch.ask(QUESTIONS["tabular"])
        records = common.read_trace(scratch.trace)[mark:]
        produced = [r for r in records if r.get("output")]
        problems = []
        if len(texts) != 1:
            problems.append("%d replies" % len(texts))
        if produced:
            problems.append("hook output under original: %s" % produced)
        if not any(r.get("handler") == "inject" for r in records):
            problems.append("no inject decision traced")
        results.append({"kind": "original", "replies": len(texts), "trace": records, "problems": problems, "pass": not problems})
        print("%-4s original replies=%d %s" % ("PASS" if not problems else "FAIL", len(texts), "; ".join(problems)), flush=True)

        # Oracle 4b: set a mode, exit, and check a brand-new session keeps it.
        scratch.mode("block", "mode → block")
        scratch.stop()
        state_file = os.path.join(scratch.xdg, "claude-fmt", "state.json")
        scratch.start()
        scratch.mode("", "current mode is block")
        result = graded("block", scratch.ask(QUESTIONS["flow"]), "persistence")
        result["state_file_used"] = os.path.exists(state_file)
        if not result["state_file_used"]:
            result["problems"].append("default XDG state file was not written")
            result["pass"] = False
        results.append(result)
        print("%-4s persistence (new session, mode block) %s" % ("PASS" if result["pass"] else "FAIL", "; ".join(result["problems"])), flush=True)
        scratch.stop()

        # Oracle 3: a forced miss is rescued once, visibly.
        scratch.start(no_inject=True)
        scratch.mode("tabular", "mode → tabular")
        texts = scratch.ask(QUESTIONS["tabular"] + PROSE)
        result = graded("tabular", texts, "forced_miss")
        if len(texts) != 2:
            result["problems"].append("expected 2 replies, got %d" % len(texts))
        elif common.check("tabular", texts[0])[0]:
            result["problems"].append("first reply already passed; nothing was rescued")
        if "Stop hook feedback" not in pane():
            result["problems"].append("'Stop hook feedback' not on screen")
        stops = [(r.get("retry"), r.get("output")) for r in common.read_trace(scratch.trace)
                 if r.get("handler") == "stop"][-2:]
        if stops != [(False, True), (True, False)]:
            result["problems"].append("Stop trace %s, expected [send-back, silent retry]" % stops)
        result["pass"] = not result["problems"]
        results.append(result)
        print("%-4s forced miss replies=%d %s" % ("PASS" if result["pass"] else "FAIL", len(texts), "; ".join(result["problems"])), flush=True)
        scratch.stop()
        scratch.assert_untouched("sessions")
    except Flake as err:
        flakes.append(str(err))
        print("FLAKE: %s" % err, flush=True)
    finally:
        scratch.cleanup()
        common.cleanup_run_dir()
        guard_ok = True
        try:
            scratch.assert_untouched("cleanup")
        except RuntimeError as err:
            guard_ok = False
            print("GUARD: %s" % err)
        leftovers = claude_fmt_traces()
        if leftovers:
            guard_ok = False
            print("GUARD: claude-fmt left behind in %s" % ", ".join(leftovers))

    common.write_json(os.path.join(out, "results.json"), {"results": results, "flakes": flakes, "guard_ok": guard_ok})
    passed = sum(1 for r in results if r["pass"])
    print("\n%d/%d checks passed, %d flakes, guard %s. Details: %s" % (
        passed, len(results), len(flakes), "ok" if guard_ok else "TRIPPED", out))
    return 0 if passed == len(results) and not flakes and guard_ok and len(results) == 9 else 1


if __name__ == "__main__":
    sys.exit(main())
