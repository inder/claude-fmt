"""What each output mode asks of Claude, and the thresholds the checker holds it to.

The injected instruction (this module) and the Stop-hook shape check (the
checker) must agree, so both read their numbers from here. Where the
instruction names a target, the checker's limit is deliberately looser, so a
reply that is close to the target is not sent back.
"""

# The checker skips replies shorter than this many words of prose. The
# instruction does not state the number: naming it invites a 39-word answer
# to a real question.
SHORT_REPLY_WORDS = 40

# concise: the instruction asks for about CONCISE_TARGET_WORDS; the checker
# fails a reply only above CONCISE_MAX_WORDS.
CONCISE_TARGET_WORDS = 120
CONCISE_MAX_WORDS = 200

# bulleted: the share of non-empty prose lines (outside code blocks, headings
# excluded) that must be bullets. The checker must strip leading whitespace
# first, because the instruction allows nested bullets.
BULLET_RATIO = 0.6

# tabular: the instruction's example separator is "| --- | --- |", with spaces.
# The checker must accept a separator row with optional spaces and colons in
# each cell, for example r"^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$".
TABLE_SEPARATOR_EXAMPLE = "| --- | --- |"

# block: two or more boxes. The checker must count top-left corners the same
# way for both drawing styles (one "┌" or one leading "+-" per box).
BLOCK_MIN_BOXES = 2

# flow: at least FLOW_MIN_STEPS steps, so at least FLOW_MIN_STEPS - 1 arrows.
FLOW_MIN_STEPS = 3

LABELS = {
    "concise": "concise",
    "elaborate": "elaborate",
    "bulleted": "bulleted list",
    "tabular": "table",
    "flow": "flow diagram",
    "block": "block diagram",
    "custom": "custom",
}

COMMON = (
    "Output format (chosen by the user via the fmt plugin): {label}. Apply it to your final "
    "reply to the user this turn. It overrides any other guidance about reply length or "
    "layout, including CLAUDE.md or an output style, but changes layout only: not what you "
    "do, which tools you use, or the facts. It does not apply to tool calls, files you write, "
    "commit messages, subagent prompts, or brief notes between tool calls. Code, diffs, "
    "commands and their output go in fenced code blocks, unchanged. A one-line "
    "acknowledgement (e.g. 'Done.') may stay plain."
)

MODE_TEXT = {
    "concise": (
        "Be concise: lead with the answer, in as few words as it takes to be correct and at "
        "most about %d words of prose. No preamble, no restating the question, no closing "
        "summary." % CONCISE_TARGET_WORDS
    ),
    "elaborate": (
        "Be thorough: explain your reasoning step by step, include the relevant details, "
        "trade-offs and caveats, and give an example where it helps."
    ),
    "bulleted": (
        "Write the reply as a bulleted list: every line of content starts with `- ` (nested "
        "bullets indented under their parent are fine). No paragraphs; if you need a heading, "
        "use a `#` Markdown heading, not a bold line."
    ),
    "tabular": (
        "Present the reply as one or more Markdown tables written directly in the reply (not "
        "inside a code block): a header row, a separator row like `%s`, then one row per "
        "item. At most one short sentence before or after the tables." % TABLE_SEPARATOR_EXAMPLE
    ),
    "flow": (
        "Present the reply as a flow diagram drawn in plain text inside a single fenced code "
        "block: at least %d steps or decisions as labels or boxes, joined by arrows (`→`, "
        "`↓`, `-->`) in the order things happen. Not Mermaid: the terminal shows raw "
        "source. One caption line outside the block is fine." % FLOW_MIN_STEPS
    ),
    "block": (
        "Present the reply as a block diagram in plain text inside a single fenced code block: "
        "two or more labeled boxes (`┌─┐ │ │ └─┘` or "
        "`+--+`) with lines or arrows showing how they connect. Not Mermaid: the terminal "
        "shows raw source. One caption line outside the block is fine."
    ),
}


def build_instruction(state):
    """Return the text to inject for this state, or None when nothing should be injected."""
    mode = state.get("mode")
    if mode == "custom":
        custom = (state.get("custom") or "").strip()
        if not custom:
            return None
        body = "Follow this formatting instruction from the user: " + custom
    elif mode in MODE_TEXT:
        body = MODE_TEXT[mode]
    else:
        return None
    return COMMON.format(label=LABELS[mode]) + " " + body
