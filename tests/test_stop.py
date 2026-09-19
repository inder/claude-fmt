import io
import json
import os
import tempfile
import time
import unittest
from unittest import mock

import helpers
import fmt_core
import fmt_modes

TABLE = (
    "| Database | Best for |\n| --- | --- |\n"
    "| SQLite | a single process on one machine, with no server to run |\n"
    "| PostgreSQL | a growing product that needs strict typing and concurrent writes |\n"
)


class StopHookTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "state.json")

    def stop(self, payload=None, extra_env=None):
        payload = helpers.fixture("stop_first") if payload is None else payload
        return helpers.run_hook("stop", payload, self.path, extra_env=extra_env)

    def send_back(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "Stop")
        self.assertNotIn("decision", out)
        return out["hookSpecificOutput"]["additionalContext"]

    def assert_silent(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_miss_in_each_checked_mode_sends_back_with_label_reason_and_rule(self):
        # The fixture's reply is two prose paragraphs: wrong for every checked
        # mode except concise.
        for mode in ("bulleted", "tabular", "flow", "block"):
            fmt_core.write_state(mode, path=self.path)
            result = self.stop()
            text = self.send_back(result)
            self.assertIn("required %s format" % fmt_modes.LABELS[mode], text, mode)
            self.assertIn(fmt_modes.MODE_TEXT[mode], text, mode)
            self.assertIn("no tool calls", text)
            self.assertIn("fmt: %s reply sent back" % mode, result.stderr)

    def test_concise_miss_sends_back(self):
        fmt_core.write_state("concise", path=self.path)
        long_reply = " ".join(["The handshake verifies the certificate and agrees on keys."] * 30)
        payload = dict(helpers.fixture("stop_first"), last_assistant_message=long_reply)
        self.assertIn("words of prose (limit", self.send_back(self.stop(payload)))

    def test_passing_reply_is_silent(self):
        fmt_core.write_state("tabular", path=self.path)
        payload = dict(helpers.fixture("stop_first"), last_assistant_message=TABLE)
        self.assert_silent(self.stop(payload))

    def test_retry_is_never_checked(self):
        fmt_core.write_state("tabular", path=self.path)
        self.assert_silent(self.stop(helpers.fixture("stop_retry")))
        # Even a wrong-shape retry is accepted: at most one send-back per turn.
        retry = dict(helpers.fixture("stop_first"), stop_hook_active=True)
        self.assert_silent(self.stop(retry))

    def test_any_truthy_retry_flag_counts_as_a_retry(self):
        fmt_core.write_state("tabular", path=self.path)
        for flag in (True, 1, "true"):
            self.assert_silent(self.stop(dict(helpers.fixture("stop_first"), stop_hook_active=flag)))

    def test_retry_guard_comes_before_reading_state(self):
        import fmt_hook

        payload = dict(helpers.fixture("stop_retry"))
        with mock.patch("fmt_core.read_state", side_effect=AssertionError("state read")):
            self.assertIsNone(fmt_hook.handle_stop(payload))

    def test_unchecked_modes_and_bad_state_are_silent(self):
        for mode in ("elaborate", "original"):
            fmt_core.write_state(mode, path=self.path)
            self.assert_silent(self.stop())
        fmt_core.write_state("custom", custom="answer as a haiku", path=self.path)
        self.assert_silent(self.stop())
        os.remove(self.path)
        self.assert_silent(self.stop())  # missing
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assert_silent(self.stop())  # corrupt

    def test_missing_empty_or_non_string_reply_is_silent(self):
        fmt_core.write_state("tabular", path=self.path)
        base = helpers.fixture("stop_first")
        for value in (None, "", "   \n", 42, ["a"]):
            self.assert_silent(self.stop(dict(base, last_assistant_message=value)))
        without = dict(base)
        del without["last_assistant_message"]
        self.assert_silent(self.stop(without))

    def test_other_events_and_bad_input_are_silent(self):
        fmt_core.write_state("tabular", path=self.path)
        self.assert_silent(self.stop(dict(helpers.fixture("stop_first"), hook_event_name="SubagentStop")))
        for stdin in ("", "not json", "[]", "null"):
            self.assert_silent(helpers.run_hook("stop", stdin, self.path))

    def test_no_inject_switch_does_not_disable_checking(self):
        fmt_core.write_state("tabular", path=self.path)
        self.send_back(self.stop(extra_env={"CLAUDE_FMT_NO_INJECT": "1"}))

    def test_clarifying_question_is_not_sent_back(self):
        fmt_core.write_state("tabular", path=self.path)
        question = (
            "Before I compare them, how many people will use the app at once, and will more than "
            "one server write to the database at the same time?"
        )
        self.assert_silent(self.stop(dict(helpers.fixture("stop_first"), last_assistant_message=question)))

    def test_checker_error_exits_silently_with_traceback(self):
        import fmt_hook

        stdin = io.TextIOWrapper(io.BytesIO(json.dumps(helpers.fixture("stop_first")).encode()))
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"CLAUDE_FMT_STATE": self.path}), mock.patch(
            "fmt_core.read_state", side_effect=RuntimeError("state bug")
        ), mock.patch.object(fmt_hook.sys, "stdin", stdin), mock.patch.object(
            fmt_hook.sys, "stdout", stdout
        ), mock.patch.object(fmt_hook.sys, "stderr", stderr):
            self.assertEqual(fmt_hook.main(["fmt_hook.py", "stop"]), 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("RuntimeError: state bug", stderr.getvalue())

    def test_large_reply_is_checked_quickly(self):
        fmt_core.write_state("tabular", path=self.path)
        big = ("The handshake verifies the certificate and agrees on keys. " * 200)[:10000]
        start = time.monotonic()
        self.send_back(self.stop(dict(helpers.fixture("stop_first"), last_assistant_message=big)))
        self.assertLess(time.monotonic() - start, 2.0)

    def test_hooks_json_registers_stop_but_not_subagent_stop(self):
        with open(os.path.join(helpers.ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
            hooks = json.load(f)["hooks"]
        self.assertIn("Stop", hooks)
        self.assertNotIn("SubagentStop", hooks)
        self.assertEqual(hooks["Stop"][0]["hooks"][0]["args"][-1], "stop")


class SendBackTextTest(unittest.TestCase):
    def test_unchecked_modes_do_not_raise(self):
        for mode in ("custom", "elaborate", "shouty"):
            self.assertIn("(why)", fmt_modes.build_send_back(mode, "why"))

    def test_every_checked_mode_has_a_send_back(self):
        import fmt_check

        for mode in fmt_check.CHECKED_MODES:
            text = fmt_modes.build_send_back(mode, "some reason")
            self.assertIn("(some reason)", text)
            self.assertIn("Start directly with the formatted answer", text)


if __name__ == "__main__":
    unittest.main()
