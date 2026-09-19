"""Mode state for the fmt plugin.

Stdlib only; supports Python 3.9+. Every entry point (hooks and the
claude-fmt CLI) resolves the same state file, so a mode set one way is
seen by all of them.
"""

import json
import os
import tempfile
import time

MODES = (
    "concise",
    "elaborate",
    "bulleted",
    "tabular",
    "flow",
    "block",
    "custom",
    "original",
)
STATE_VERSION = 1
# The mode instruction is injected as context, which Claude Code caps at
# 10,000 characters per hook; keep custom text well inside that.
MAX_CUSTOM_CHARS = 2000

_QUOTE_PAIRS = (('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’"))


def state_path():
    """Return the state file path. CLAUDE_FMT_STATE overrides it (tests, harness)."""
    override = os.environ.get("CLAUDE_FMT_STATE")
    if override:
        return override
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    return os.path.join(base, "claude-fmt", "state.json")


def default_state():
    return {"version": STATE_VERSION, "mode": "original", "custom": ""}


def read_state(path=None):
    """Read the state file. Anything missing, corrupt or unknown reads as `original`."""
    path = path or state_path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return default_state()
    if not isinstance(data, dict):
        return default_state()
    mode = data.get("mode")
    custom = data.get("custom")
    if mode not in MODES:
        return default_state()
    if not isinstance(custom, str):
        custom = ""
    if mode == "custom" and not custom.strip():
        return default_state()
    state = default_state()
    state.update(mode=mode, custom=custom if mode == "custom" else "")
    if isinstance(data.get("updated_at"), str):
        state["updated_at"] = data["updated_at"]
    return state


def write_state(mode, custom="", path=None):
    """Write the state atomically: temp file in the same directory, then rename."""
    path = path or state_path()
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    state = {
        "version": STATE_VERSION,
        "mode": mode,
        "custom": custom if mode == "custom" else "",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    fd, tmp = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return state


def _strip_outer_quotes(text):
    for open_q, close_q in _QUOTE_PAIRS:
        if len(text) >= 2 and text.startswith(open_q) and text.endswith(close_q):
            return text[len(open_q) : -len(close_q)].strip()
    return text


def parse_mode_args(args):
    """Parse `/fmt:mode` arguments.

    Returns None when there are no arguments (show the current mode), or a
    (mode, custom) tuple. Raises ValueError with a user-facing message.
    """
    args = (args or "").strip()
    if not args:
        return None
    parts = args.split(None, 1)
    head = parts[0]
    rest = parts[1].strip() if len(parts) > 1 else ""
    mode = head.lower()
    if mode not in MODES:
        raise ValueError("unknown mode '%s'" % head)
    if mode == "custom":
        custom = _strip_outer_quotes(rest)
        if not custom:
            raise ValueError('custom needs an instruction, e.g. /fmt:mode custom "answer as a haiku"')
        if len(custom) > MAX_CUSTOM_CHARS:
            raise ValueError(
                "custom instruction is %d characters; the limit is %d"
                % (len(custom), MAX_CUSTOM_CHARS)
            )
        return mode, custom
    if rest:
        raise ValueError("'%s' takes no extra text (got '%s')" % (mode, rest))
    return mode, ""


def describe(state):
    if state["mode"] == "custom":
        return 'custom ("%s")' % state["custom"]
    return state["mode"]


def modes_hint():
    return "Modes: %s. Use custom \"<instruction>\" for your own format." % ", ".join(
        m for m in MODES if m != "custom"
    )


def run_mode_command(args, path=None):
    """Apply `/fmt:mode <args>`.

    Returns (ok, message): ok is False when the mode could not be changed,
    and message is what to show the user either way.
    """
    try:
        parsed = parse_mode_args(args)
    except ValueError as err:
        return False, "fmt: %s. Mode unchanged. %s" % (err, modes_hint())
    if parsed is None:
        return True, "fmt: current mode is %s. %s" % (describe(read_state(path)), modes_hint())
    mode, custom = parsed
    try:
        state = write_state(mode, custom, path)
    except OSError as err:
        return False, "fmt: could not save the mode (%s). Mode unchanged." % (err.strerror or err)
    return True, "fmt: mode \u2192 %s" % describe(state)
