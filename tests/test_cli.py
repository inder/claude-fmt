import os
import tempfile
import unittest

import helpers


class CliTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "state.json")

    def test_round_trip(self):
        result = helpers.run_cli(["mode", "tabular"], self.path)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "fmt: mode → tabular")
        self.assertIn("current mode is tabular", helpers.run_cli(["get"], self.path).stdout)

    def test_no_arguments_prints_current_mode(self):
        result = helpers.run_cli([], self.path)
        self.assertEqual(result.returncode, 0)
        self.assertIn("current mode is original", result.stdout)

    def test_custom_from_shell_words(self):
        # The shell has already removed the quotes by the time argv arrives.
        result = helpers.run_cli(["mode", "custom", "don't", "use", "jargon"], self.path)
        self.assertEqual(result.returncode, 0)
        self.assertIn('custom ("don\'t use jargon")', result.stdout)

    def test_invalid_mode_exits_nonzero(self):
        result = helpers.run_cli(["mode", "shouty"], self.path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Mode unchanged", result.stdout)

    def test_reset_returns_to_original(self):
        helpers.run_cli(["mode", "flow"], self.path)
        helpers.run_cli(["reset"], self.path)
        self.assertIn("current mode is original", helpers.run_cli(["get"], self.path).stdout)

    def test_path_prints_the_override(self):
        self.assertEqual(helpers.run_cli(["path"], self.path).stdout.strip(), self.path)

    def test_unknown_subcommand_exits_2(self):
        self.assertEqual(helpers.run_cli(["frobnicate"], self.path).returncode, 2)

    def test_works_through_a_symlink(self):
        link = os.path.join(tempfile.mkdtemp(), "claude-fmt")
        os.symlink(helpers.CLI, link)
        result = helpers.run_cli(["mode", "block"], self.path, executable=link)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mode → block", result.stdout)

    def test_runs_through_its_own_shebang(self):
        self.assertTrue(os.access(helpers.CLI, os.X_OK))
        result = helpers.run_cli(["mode", "concise"], self.path, via_shebang=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mode \u2192 concise", result.stdout)

    def test_legacy_locale_output_does_not_crash_after_saving(self):
        result = helpers.run_cli(
            ["mode", "tabular"], self.path, extra_env={"PYTHONIOENCODING": "iso-8859-1"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fmt: mode ? tabular", result.stdout)
        self.assertIn("current mode is tabular", helpers.run_cli(["get"], self.path).stdout)


if __name__ == "__main__":
    unittest.main()
