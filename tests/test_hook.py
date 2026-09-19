import json
import os
import tempfile
import time
import unittest

import helpers
import fmt_core


class ExpandHookTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "state.json")

    def expand(self, payload):
        return helpers.run_hook("expand", payload, self.path)

    def assert_silent(self, result):
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_sets_mode_from_real_captured_payload_and_blocks(self):
        result = self.expand(helpers.fixture("expansion_tabular"))
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)
        self.assertEqual(out, {"decision": "block", "reason": "fmt: mode → tabular"})
        self.assertEqual(fmt_core.read_state(self.path)["mode"], "tabular")

    def test_custom_from_real_captured_payload(self):
        result = self.expand(helpers.fixture("expansion_custom"))
        out = json.loads(result.stdout)
        self.assertEqual(out["reason"], 'fmt: mode → custom ("don\'t use jargon")')
        self.assertEqual(fmt_core.read_state(self.path)["custom"], "don't use jargon")

    def test_empty_args_show_current_mode_and_modes(self):
        fmt_core.write_state("flow", path=self.path)
        out = json.loads(self.expand(helpers.fixture("expansion_empty")).stdout)
        self.assertEqual(out["decision"], "block")
        self.assertTrue(out["reason"].startswith("fmt: current mode is flow."), out["reason"])
        self.assertIn("Modes:", out["reason"])

    def test_invalid_mode_blocks_with_error_and_keeps_state(self):
        fmt_core.write_state("concise", path=self.path)
        payload = dict(helpers.fixture("expansion_tabular"), command_args="shouty")
        out = json.loads(self.expand(payload).stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("unknown mode 'shouty'", out["reason"])
        self.assertEqual(fmt_core.read_state(self.path)["mode"], "concise")

    def test_ignores_other_commands_sources_and_events(self):
        base = helpers.fixture("expansion_tabular")
        for change in (
            {"command_name": "other:mode"},
            {"command_name": "mode"},
            {"command_source": "user"},
            {"hook_event_name": "UserPromptSubmit"},
        ):
            self.assert_silent(self.expand(dict(base, **change)))
        self.assertEqual(fmt_core.read_state(self.path)["mode"], "original")

    def test_bad_input_exits_silently(self):
        for stdin in ("", "   \n", "not json", "[1, 2]", "null", '{"hook_event_name": 5}'):
            self.assert_silent(self.expand(stdin))

    def test_missing_or_non_string_args_show_current_mode(self):
        base = helpers.fixture("expansion_tabular")
        for args in (None, 42):
            out = json.loads(self.expand(dict(base, command_args=args)).stdout)
            self.assertTrue(out["reason"].startswith("fmt: current mode is"), out["reason"])

    def test_unknown_event_argument_exits_silently(self):
        result = helpers.run_hook("nope", helpers.fixture("expansion_tabular"), self.path)
        self.assert_silent(result)

    def test_runs_well_under_one_second(self):
        start = time.monotonic()
        self.expand(helpers.fixture("expansion_tabular"))
        self.assertLess(time.monotonic() - start, 1.0)

    def test_hook_and_cli_share_the_state_file(self):
        self.expand(helpers.fixture("expansion_tabular"))
        result = helpers.run_cli(["get"], self.path)
        self.assertIn("current mode is tabular", result.stdout)
        helpers.run_cli(["mode", "bulleted"], self.path)
        out = json.loads(self.expand(helpers.fixture("expansion_empty")).stdout)
        self.assertIn("current mode is bulleted", out["reason"])


if __name__ == "__main__":
    unittest.main()
