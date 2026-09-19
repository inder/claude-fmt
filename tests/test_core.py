import json
import os
import stat
import tempfile
import unittest
from unittest import mock

import helpers  # noqa: F401  (puts lib/ on sys.path)
import fmt_core


class StatePathTest(unittest.TestCase):
    def test_override_wins(self):
        with mock.patch.dict(os.environ, {"CLAUDE_FMT_STATE": "/tmp/x/state.json"}):
            self.assertEqual(fmt_core.state_path(), "/tmp/x/state.json")

    def test_xdg_config_home(self):
        env = {"XDG_CONFIG_HOME": "/tmp/xdg"}
        with mock.patch.dict(os.environ, env):
            os.environ.pop("CLAUDE_FMT_STATE", None)
            self.assertEqual(fmt_core.state_path(), "/tmp/xdg/claude-fmt/state.json")

    def test_default_is_dot_config(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_FMT_STATE", None)
            os.environ.pop("XDG_CONFIG_HOME", None)
            expected = os.path.join(os.path.expanduser("~"), ".config", "claude-fmt", "state.json")
            self.assertEqual(fmt_core.state_path(), expected)


class ReadWriteTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "nested", "claude-fmt", "state.json")

    def write_raw(self, text):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_missing_reads_as_original(self):
        self.assertEqual(fmt_core.read_state(self.path)["mode"], "original")

    def test_corrupt_reads_as_original_and_set_overwrites(self):
        self.write_raw("{not json")
        self.assertEqual(fmt_core.read_state(self.path)["mode"], "original")
        fmt_core.write_state("tabular", path=self.path)
        self.assertEqual(fmt_core.read_state(self.path)["mode"], "tabular")

    def test_non_dict_unknown_mode_and_empty_custom_read_as_original(self):
        for raw in ("[1, 2]", '{"mode": "shouty"}', '{"mode": "custom", "custom": "  "}', '"tabular"'):
            self.write_raw(raw)
            self.assertEqual(fmt_core.read_state(self.path)["mode"], "original", raw)

    def test_write_creates_parents_and_leaves_no_temp_file(self):
        fmt_core.write_state("bulleted", path=self.path)
        directory = os.path.dirname(self.path)
        self.assertEqual(os.listdir(directory), ["state.json"])

    def test_state_has_version_and_updated_at(self):
        fmt_core.write_state("flow", path=self.path)
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["version"], fmt_core.STATE_VERSION)
        self.assertRegex(data["updated_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(data["custom"], "")

    def test_hand_edited_custom_text_is_clamped(self):
        self.write_raw(json.dumps({"mode": "custom", "custom": "y" * (fmt_core.MAX_CUSTOM_CHARS + 500)}))
        self.assertEqual(len(fmt_core.read_state(self.path)["custom"]), fmt_core.MAX_CUSTOM_CHARS)

    def test_custom_text_only_kept_for_custom_mode(self):
        fmt_core.write_state("tabular", custom="ignored", path=self.path)
        self.assertEqual(fmt_core.read_state(self.path)["custom"], "")
        fmt_core.write_state("custom", custom="answer as a haiku", path=self.path)
        self.assertEqual(fmt_core.read_state(self.path)["custom"], "answer as a haiku")


class ParseTest(unittest.TestCase):
    def test_empty_means_show(self):
        for args in ("", "   ", None, "\t\n"):
            self.assertIsNone(fmt_core.parse_mode_args(args))

    def test_every_plain_mode_parses(self):
        for mode in fmt_core.MODES:
            if mode != "custom":
                self.assertEqual(fmt_core.parse_mode_args(mode), (mode, ""))

    def test_case_is_normalized(self):
        self.assertEqual(fmt_core.parse_mode_args("TABULAR"), ("tabular", ""))

    def test_tabs_and_extra_spaces(self):
        self.assertEqual(fmt_core.parse_mode_args("  \tbulleted  "), ("bulleted", ""))

    def test_unknown_mode_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown mode 'shouty'"):
            fmt_core.parse_mode_args("shouty")

    def test_extra_text_on_plain_mode_rejected(self):
        with self.assertRaisesRegex(ValueError, "takes no extra text"):
            fmt_core.parse_mode_args("tabular please")

    def test_custom_quotes_stripped(self):
        cases = {
            'custom "answer as a haiku"': "answer as a haiku",
            "custom 'answer as a haiku'": "answer as a haiku",
            "custom \u201canswer as a haiku\u201d": "answer as a haiku",
            "custom answer as a haiku": "answer as a haiku",
            'custom "don\'t use jargon"': "don't use jargon",
            'custom "keep "inner" quotes"': 'keep "inner" quotes',
        }
        for args, expected in cases.items():
            self.assertEqual(fmt_core.parse_mode_args(args), ("custom", expected), args)

    def test_custom_mismatched_quotes_kept_verbatim(self):
        self.assertEqual(fmt_core.parse_mode_args("custom \"half"), ("custom", '"half'))

    def test_custom_without_text_rejected(self):
        for args in ("custom", 'custom ""', "custom '   '"):
            with self.assertRaisesRegex(ValueError, "needs an instruction"):
                fmt_core.parse_mode_args(args)

    def test_custom_length_boundary(self):
        at_limit = "x" * fmt_core.MAX_CUSTOM_CHARS
        self.assertEqual(fmt_core.parse_mode_args("custom " + at_limit), ("custom", at_limit))
        with self.assertRaisesRegex(ValueError, "the limit is"):
            fmt_core.parse_mode_args("custom " + at_limit + "x")


class RunModeCommandTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "state.json")

    def test_set_then_show(self):
        ok, message = fmt_core.run_mode_command("tabular", self.path)
        self.assertTrue(ok)
        self.assertEqual(message, "fmt: mode \u2192 tabular")
        ok, message = fmt_core.run_mode_command("", self.path)
        self.assertTrue(ok)
        self.assertTrue(message.startswith("fmt: current mode is tabular."), message)

    def test_invalid_mode_leaves_state_unchanged(self):
        fmt_core.run_mode_command("bulleted", self.path)
        ok, message = fmt_core.run_mode_command("shouty", self.path)
        self.assertFalse(ok)
        self.assertIn("Mode unchanged", message)
        self.assertIn("Modes: concise", message)
        self.assertEqual(fmt_core.read_state(self.path)["mode"], "bulleted")

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root ignores permissions")
    def test_unwritable_directory_reports_and_leaves_state(self):
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, "state.json")
        fmt_core.write_state("concise", path=path)
        os.chmod(directory, stat.S_IRUSR | stat.S_IXUSR)
        try:
            ok, message = fmt_core.run_mode_command("tabular", path)
        finally:
            os.chmod(directory, stat.S_IRWXU)
        self.assertFalse(ok)
        self.assertIn("could not save the mode", message)
        self.assertEqual(fmt_core.read_state(path)["mode"], "concise")


if __name__ == "__main__":
    unittest.main()
