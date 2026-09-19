import unittest
from unittest import mock

import helpers  # noqa: F401  (puts lib/ on sys.path)
import fmt_check as K
import fmt_modes as M

FILLER = (
    "The browser resolves the name, opens a connection, checks the certificate and agrees on "
    "session keys before any request is sent, so everything after the handshake is encrypted. "
)


def prose(words):
    """Return roughly `words` words of plain prose."""
    base = FILLER.split()
    return " ".join((base * (words // len(base) + 1))[:words])


class SplitBlocksTest(unittest.TestCase):
    def test_indented_tilde_and_unclosed_fences(self):
        text = "intro\n  ```text\n  a -> b\n  ```\n~~~~\nx\n~~~~\n```\nnever closed\n"
        prose_lines, fences = K.split_blocks(text)
        self.assertEqual([f.info_word for f in fences], ["text", "", ""])
        self.assertEqual(fences[2].lines, ["never closed", ""])
        self.assertEqual([p for p in prose_lines if p is not None], ["intro"])

    def test_backtick_info_with_backtick_is_not_a_fence(self):
        _, fences = K.split_blocks("``` a `b` c\nnot code\n")
        self.assertEqual(fences, [])

    def test_crlf_is_normalized(self):
        prose_lines, fences = K.split_blocks("a\r\n```\r\nb\r\n```\r\n")
        self.assertEqual(fences[0].lines, ["b"])

    def test_info_word_is_case_insensitive_first_token(self):
        _, fences = K.split_blocks("```TEXT title=x\na -> b -> c\n```\n")
        self.assertTrue(fences[0].can_be_diagram)

    def test_unfamiliar_fence_labels_can_be_diagrams(self):
        for label in ("ascii-art", "flowchart", "Diagram", "none"):
            _, fences = K.split_blocks("```%s\na -> b -> c\n```\n" % label)
            self.assertTrue(fences[0].can_be_diagram, label)

    def test_mermaid_first_line_needs_real_mermaid_syntax(self):
        for first, expected in (
            ("graph TD", True), ("flowchart LR", True), ("sequenceDiagram", True),
            ("gantt", True), ("flowchart of the handshake", False), ("graph: setup", False),
            ("mindmap of topics", False),
        ):
            _, fences = K.split_blocks("```\n%s\n  A --> B\n```\n" % first)
            self.assertEqual(fences[0].is_mermaid, expected, first)
        _, fences = K.split_blocks("```python\ngraph = build(deps)\n```\n")
        self.assertFalse(fences[0].is_mermaid)

    def test_language_fence_is_not_a_diagram(self):
        _, fences = K.split_blocks("```js\nconst f = (a) => a;\n```\n")
        self.assertFalse(fences[0].can_be_diagram)


class CountingTest(unittest.TestCase):
    def test_arrows(self):
        self.assertEqual(K.count_arrows(["a ─> b ═> c"]), 2)
        self.assertEqual(K.count_arrows(["   v      v"]), 2)
        self.assertEqual(K.count_arrows(["a <-> b"]), 1)
        self.assertEqual(K.count_arrows(["a → b ↓"]), 2)
        self.assertEqual(K.count_arrows(["plain words only"]), 0)

    def test_boxes(self):
        single = ["+------+", "| web  |", "+------+"]
        self.assertEqual(K.count_boxes(single), 1)
        self.assertEqual(K.count_boxes(["+--+--+", "|a |b |", "+--+--+"]), 2)
        self.assertEqual(K.count_boxes(["+---+  +---+", "| a |  | b |", "+---+  +---+"]), 2)
        stacked = ["┌──┐", "│a │", "├──┤", "│b │", "└──┘"]
        self.assertEqual(K.count_boxes(stacked), 2)
        self.assertEqual(K.count_boxes(["┌─┐", "└─┘"]), 1)


class CheckTest(unittest.TestCase):
    def test_unchecked_modes_and_bad_input_pass(self):
        for mode in ("elaborate", "custom", "original", "shouty"):
            self.assertEqual(K.check(mode, prose(300)), (True, "not checked"))
        self.assertEqual(K.check("tabular", None), (True, "not checked"))

    def test_checker_errors_pass(self):
        with mock.patch.object(K, "split_blocks", side_effect=RuntimeError("boom")):
            ok, reason = K.check("tabular", prose(100))
        self.assertTrue(ok)
        self.assertIn("checker error", reason)

    def test_short_prose_with_a_long_code_block_is_a_short_reply(self):
        text = prose(39) + "\n\n```bash\n" + "echo step\n" * 100 + "```\n"
        for mode in ("tabular", "bulleted", "concise"):
            self.assertEqual(K.check(mode, text), (True, "short reply"), mode)

    def test_mermaid_fails_diagram_modes_even_when_short(self):
        text = "```mermaid\nflowchart LR\n  A --> B --> C\n```\n"
        for mode in ("flow", "block"):
            ok, reason = K.check(mode, text)
            self.assertFalse(ok, mode)
            self.assertIn("Mermaid", reason)

    def test_mermaid_next_to_a_valid_text_diagram_passes(self):
        text = "```mermaid\ngraph TD\n A-->B\n```\n\n```\nA → B → C\n```\n" + prose(60)
        self.assertEqual(K.check("flow", text), (True, "flow diagram"))

    def test_concise_limit_boundary(self):
        self.assertTrue(K.check("concise", prose(M.CONCISE_MAX_WORDS))[0])
        ok, reason = K.check("concise", prose(M.CONCISE_MAX_WORDS + 1))
        self.assertFalse(ok)
        self.assertIn("limit %d" % M.CONCISE_MAX_WORDS, reason)

    def test_concise_ignores_code(self):
        text = prose(190) + "\n\n```python\n" + "value = compute(x)\n" * 200 + "```\n"
        self.assertTrue(K.check("concise", text)[0])

    def test_bullet_ratio_boundary(self):
        lines = ["- point %d about the handshake and keys" % i for i in range(6)]
        lines += ["A plain sentence about certificates and keys here." for _ in range(4)]
        self.assertTrue(K.check("bulleted", "\n".join(lines))[0])  # exactly 60%
        lines.append("One more plain sentence tips it under the ratio.")
        self.assertFalse(K.check("bulleted", "\n".join(lines))[0])

    def test_numbered_items_count_as_bullets(self):
        text = "\n".join("%d. step %d of the handshake, where keys and certificates matter" % (i, i) for i in range(1, 7))
        self.assertTrue(K.check("bulleted", text)[0])

    def test_table_with_a_few_caveats_passes(self):
        rows = "\n".join("| item %d | detail about certificates and session keys |" % i for i in range(8))
        text = "| Item | Detail |\n| --- | --- |\n" + rows + "\n\n" + prose(70)
        self.assertEqual(K.check("tabular", text), (True, "table"))

    def test_table_prose_rule_needs_both_limits(self):
        rows = "\n".join("| item %d | %s |" % (i, prose(20)) for i in range(8))
        text = "| Item | Detail |\n| --- | --- |\n" + rows + "\n\n" + prose(120)
        self.assertEqual(K.check("tabular", text), (True, "table"))  # prose > 80 but < table words

    def test_every_checked_mode_is_known_to_fmt_modes(self):
        self.assertLessEqual(set(K.CHECKED_MODES), set(M.MODE_TEXT))


if __name__ == "__main__":
    unittest.main()
