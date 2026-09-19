"""Hook entry point for the fmt plugin.

Usage: python3 fmt_hook.py <event>, with the hook's JSON input on stdin.

Fails open: any unexpected error exits 0 with no output, so Claude Code
carries on as if the plugin were not installed.
"""

import json
import os
import re
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

MODE_COMMAND = "fmt:mode"


def handle_expand(payload):
    """UserPromptExpansion: apply `/fmt:mode` and block it so the model never runs."""
    if payload.get("hook_event_name") != "UserPromptExpansion":
        return None
    if payload.get("command_source") != "plugin":
        return None
    if payload.get("command_name") != MODE_COMMAND:
        return None
    args = payload.get("command_args")
    if not isinstance(args, str):
        args = ""
    from fmt_core import run_mode_command

    _, message = run_mode_command(args)
    return {"decision": "block", "reason": message}


# A prompt that is itself a mode command. It reaches UserPromptSubmit only when
# the expansion hook did not handle it, and injecting then would carry the mode
# that is about to be replaced. "/mode" is included because Claude Code
# resolves an unqualified "/mode" to fmt:mode when no other skill has that name.
_MODE_COMMAND_PROMPT = re.compile(r"^\s*/(fmt:|mode(\s|$))")


def handle_inject(payload):
    """UserPromptSubmit: add the active mode's formatting instruction to Claude's context."""
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return None
    if os.environ.get("CLAUDE_FMT_NO_INJECT") == "1":
        return None
    prompt = payload.get("prompt")
    if isinstance(prompt, str) and _MODE_COMMAND_PROMPT.match(prompt):
        return None
    from fmt_core import read_state
    from fmt_modes import build_instruction

    instruction = build_instruction(read_state())
    if instruction is None:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": instruction,
        }
    }


def handle_stop(payload):
    """Stop: if the final reply missed the mode's shape, send it back once to be re-sent."""
    if payload.get("hook_event_name") != "Stop":
        return None
    # The reply that follows our send-back is never checked, so there is at
    # most one retry per turn. Checked before reading any state.
    if payload.get("stop_hook_active"):
        return None
    from fmt_check import CHECKED_MODES, check
    from fmt_core import read_state
    from fmt_modes import build_send_back

    mode = read_state().get("mode")
    if mode not in CHECKED_MODES:
        return None
    text = payload.get("last_assistant_message")
    if not isinstance(text, str) or not text.strip():
        return None
    ok, reason = check(mode, text)
    if ok:
        return None
    # Debug-only diagnostic: which mode missed and why.
    sys.stderr.write("fmt: %s reply sent back: %s\n" % (mode, reason))
    return {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": build_send_back(mode, reason),
        }
    }


HANDLERS = {"expand": handle_expand, "inject": handle_inject, "stop": handle_stop}


def _trace(handler, payload, result):
    """Append this hook's decision to $CLAUDE_FMT_TRACE, if set.

    Test-only: the live harness uses it to show directly what each hook did
    (for example, that `original` produced no output) instead of inferring it
    from the absence of text. Never raises.
    """
    path = os.environ.get("CLAUDE_FMT_TRACE")
    if not path:
        return
    try:
        from fmt_core import read_state

        record = {
            "handler": handler,
            "event": payload.get("hook_event_name"),
            "mode": read_state().get("mode"),
            "output": result is not None,
            "retry": bool(payload.get("stop_hook_active")),
        }
        if result is not None:
            record["kind"] = "block" if result.get("decision") == "block" else "context"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def main(argv):
    try:
        handler = HANDLERS.get(argv[1] if len(argv) > 1 else "")
        if handler is None:
            return 0
        raw = sys.stdin.buffer.read().decode("utf-8", "replace")
        if not raw.strip():
            return 0
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0
        result = handler(payload)
        if result is not None:
            sys.stdout.write(json.dumps(result))
        _trace(argv[1], payload, result)
    except Exception:
        # Stderr on exit 0 only shows in Claude Code's debug output, which is
        # where someone chasing a bug would look.
        traceback.print_exc()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
