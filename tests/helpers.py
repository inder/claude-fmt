import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "lib")
HOOK = os.path.join(LIB, "fmt_hook.py")
CLI = os.path.join(ROOT, "bin", "claude-fmt")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

if LIB not in sys.path:
    sys.path.insert(0, LIB)


def fixture(name):
    with open(os.path.join(FIXTURES, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def run_hook(event, stdin, state_path, extra_env=None):
    env = dict(os.environ, CLAUDE_FMT_STATE=state_path)
    env.update(extra_env or {})
    if not isinstance(stdin, (str, bytes)):
        stdin = json.dumps(stdin, ensure_ascii=False)
    if isinstance(stdin, str):
        stdin = stdin.encode("utf-8")
    result = subprocess.run(
        [sys.executable, HOOK, event],
        input=stdin,
        capture_output=True,
        env=env,
        timeout=10,
    )
    result.stdout = result.stdout.decode("utf-8")
    result.stderr = result.stderr.decode("utf-8", "replace")
    return result


def run_cli(args, state_path, executable=CLI, extra_env=None, via_shebang=False):
    env = dict(os.environ, CLAUDE_FMT_STATE=state_path)
    env.update(extra_env or {})
    command = [executable] if via_shebang else [sys.executable, executable]
    result = subprocess.run(
        command + list(args),
        capture_output=True,
        env=env,
        timeout=10,
    )
    result.stdout = result.stdout.decode("utf-8", "replace")
    result.stderr = result.stderr.decode("utf-8", "replace")
    return result
