"""Hook entry point for the fmt plugin.

Usage: python3 fmt_hook.py <event>, with the hook's JSON input on stdin.

Fails open: any unexpected error exits 0 with no output, so Claude Code
carries on as if the plugin were not installed.
"""

import json
import os
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


HANDLERS = {"expand": handle_expand}


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
    except Exception:
        # Stderr on exit 0 only shows in Claude Code's debug output, which is
        # where someone chasing a bug would look.
        traceback.print_exc()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
