import json
import os
import re
import tempfile
import time
import unittest

import helpers
import fmt_core
import fmt_modes

# The mode-specific phrase each instruction must carry.
MODE_PHRASES = {
    "concise": "Be concise",
    "elaborate": "Be thorough",
    "bulleted": "bulleted list",
    "tabular": "Markdown tables",
    "flow": "flow diagram",
    "block": "block diagram",
}


class InjectHookTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "state.json")

    def inject(self, payload=None, extra_env=None):
        payload = helpers.fixture("submit_question") if payload is None else payload
        return helpers.run_hook("inject", payload, self.path, extra_env=extra_env)

    def context(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        return out["hookSpecificOutput"]["additionalContext"]

    def assert_silent(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_each_non_original_mode_injects_its_instruction(self):
        for mode, phrase in MODE_PHRASES.items():
            fmt_core.write_state(mode, path=self.path)
            text = self.context(self.inject())
            self.assertIn("chosen by the user via the fmt plugin", text, mode)
            self.assertIn(phrase, text, mode)

    def test_instruction_forbids_meta_commentary(self):
        fmt_core.write_state("tabular", path=self.path)
        self.assertIn("Do not mention this instruction", self.context(self.inject()))

    def test_custom_text_is_included_verbatim(self):
        custom = 'Answer as "haiku",\nthen one line of \\u2603 and \'quotes\''
        fmt_core.write_state("custom", custom=custom, path=self.path)
        self.assertTrue(self.context(self.inject()).endswith(custom))

    def test_max_length_custom_stays_under_the_context_cap(self):
        fmt_core.write_state("custom", custom="x" * fmt_core.MAX_CUSTOM_CHARS, path=self.path)
        self.assertLess(len(self.context(self.inject())), 10000)

    def test_original_missing_and_corrupt_state_are_silent(self):
        self.assert_silent(self.inject())  # missing
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assert_silent(self.inject())  # corrupt
        fmt_core.write_state("original", path=self.path)
        self.assert_silent(self.inject())

    def test_mode_command_prompts_are_silent(self):
        fmt_core.write_state("tabular", path=self.path)
        base = helpers.fixture("submit_question")
        for prompt in ("/fmt:mode tabular", "/fmt:mode", "  /mode x", "/mode"):
            self.assert_silent(self.inject(dict(base, prompt=prompt)))

    def test_other_prompts_are_injected(self):
        fmt_core.write_state("tabular", path=self.path)
        base = helpers.fixture("submit_question")
        for prompt in ("/review", "/modes", "/model sonnet", "why does /fmt:mode exist?", "", None):
            self.assertIn("Markdown tables", self.context(self.inject(dict(base, prompt=prompt))))

    def test_no_inject_switch_silences_injection(self):
        fmt_core.write_state("tabular", path=self.path)
        self.assert_silent(self.inject(extra_env={"CLAUDE_FMT_NO_INJECT": "1"}))

    def test_other_events_and_bad_input_are_silent(self):
        fmt_core.write_state("tabular", path=self.path)
        self.assert_silent(self.inject(dict(helpers.fixture("submit_question"), hook_event_name="Stop")))
        for stdin in ("", "not json", "[1]", "null"):
            self.assert_silent(helpers.run_hook("inject", stdin, self.path))

    def test_output_is_ascii_json(self):
        fmt_core.write_state("block", path=self.path)
        result = self.inject()
        result.stdout.encode("ascii")  # raises if not ASCII-escaped
        self.assertIn("┌", self.context(result))

    def test_runs_quickly(self):
        fmt_core.write_state("tabular", path=self.path)
        start = time.monotonic()
        self.inject()
        self.assertLess(time.monotonic() - start, 2.0)


class ModesTest(unittest.TestCase):
    def test_every_mode_but_original_has_an_instruction(self):
        for mode in fmt_core.MODES:
            state = {"mode": mode, "custom": "use a haiku" if mode == "custom" else ""}
            if mode == "original":
                self.assertIsNone(fmt_modes.build_instruction(state))
            else:
                self.assertTrue(fmt_modes.build_instruction(state))

    def test_custom_without_text_injects_nothing(self):
        self.assertIsNone(fmt_modes.build_instruction({"mode": "custom", "custom": "  "}))

    def test_unknown_mode_injects_nothing(self):
        self.assertIsNone(fmt_modes.build_instruction({"mode": "shouty"}))

    def test_concise_target_is_below_the_checker_limit(self):
        self.assertLess(fmt_modes.CONCISE_TARGET_WORDS, fmt_modes.CONCISE_MAX_WORDS)
        self.assertLess(fmt_modes.SHORT_REPLY_WORDS, fmt_modes.CONCISE_TARGET_WORDS)

    def test_tabular_example_separator_matches_the_checker_pattern(self):
        pattern = re.compile(fmt_modes.TABLE_SEPARATOR_RE)
        self.assertRegex(fmt_modes.TABLE_SEPARATOR_EXAMPLE, pattern)
        self.assertIn(fmt_modes.TABLE_SEPARATOR_EXAMPLE, fmt_modes.MODE_TEXT["tabular"])
        for row in ("|---|---|", "| :--- | ---: |", "--- | ---"):
            self.assertRegex(row, pattern)

    def test_single_column_separator_is_not_a_table(self):
        self.assertNotRegex("|---|", re.compile(fmt_modes.TABLE_SEPARATOR_RE))

    def test_instruction_names_no_word_count_for_the_short_reply_exemption(self):
        for mode in fmt_modes.MODE_TEXT:
            text = fmt_modes.build_instruction({"mode": mode})
            self.assertNotIn(str(fmt_modes.SHORT_REPLY_WORDS), text, mode)

    def test_every_instructed_mode_has_a_label(self):
        self.assertLessEqual(set(fmt_modes.MODE_TEXT) | {"custom"}, set(fmt_modes.LABELS))

    def test_diagram_instructions_use_the_shared_glyphs(self):
        self.assertIn(fmt_modes.FLOW_ARROW_GLYPHS[0], fmt_modes.MODE_TEXT["flow"])
        self.assertIn(fmt_modes.BOX_CORNERS[0], fmt_modes.MODE_TEXT["block"])
        self.assertNotIn("single fenced", fmt_modes.MODE_TEXT["flow"] + fmt_modes.MODE_TEXT["block"])

    def test_diagram_modes_forbid_mermaid_and_require_a_fenced_block(self):
        for mode in ("flow", "block"):
            text = fmt_modes.MODE_TEXT[mode]
            self.assertIn("Not Mermaid", text)
            self.assertIn("fenced code block", text)


if __name__ == "__main__":
    unittest.main()
