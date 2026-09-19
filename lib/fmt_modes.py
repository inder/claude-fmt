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
# The checker matches separator rows with TABLE_SEPARATOR_RE, which allows
# optional spaces, alignment colons and any number of dashes per cell
# ("|:-|--:|" is valid Markdown). A single-column table ("|---|") is
# deliberately not recognized.
TABLE_SEPARATOR_EXAMPLE = "| --- | --- |"
TABLE_SEPARATOR_RE = r"^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$"

# tabular: prose outside the tables fails the check only when it is both
# longer than this and longer than the tables themselves, so a table answer
# with a few caveat lines is not sent back.
TABULAR_MAX_PROSE_WORDS = 80

# flow: at least FLOW_MIN_STEPS steps, so at least FLOW_MIN_STEPS - 1 arrows,
# inside a fenced block. The instruction names the first few glyphs; the
# checker accepts all of them plus ASCII arrows (->, -->, =>) and a line that
# is only "v" (an ASCII down-arrow under a "|").
FLOW_MIN_STEPS = 3
FLOW_ARROW_GLYPHS = ("\u2192", "\u2193", "\u2190", "\u2191", "\u27f6", "\u25b6", "\u25bc", "\u25ba", "\u25b8", "\u25be")

# block: two or more boxes inside a fenced block. Unicode boxes are counted by
# top-left corners plus tee junctions, because stacked layers ("┌─┐ ├─┤ └─┘")
# and boxes sharing a border ("┌─┬─┐") draw several boxes from one corner.
# ASCII boxes are counted as border segments "+--+" found with overlapping
# matches (so "+---+---+" is two segments), divided by two for top and bottom
# borders, rounded up. The larger of the two counts is used. Counting a
# leading "+-" per line is wrong both ways: one box has two such lines, and
# two side-by-side boxes share one line. Known false passes, accepted because
# the check leans toward passing: a directory tree ("├──") and an ASCII table
# inside a fence.
BLOCK_MIN_BOXES = 2
BOX_CORNERS = ("\u250c", "\u256d", "\u2554", "\u250f", "\u2552", "\u2553")
BOX_TEES = ("\u252c", "\u251c", "\u253c", "\u2566", "\u2560", "\u2533", "\u2523", "\u2564", "\u255f")

# A fence counts as a possible diagram when its info string's first word
# (case-insensitive) is empty or one of these. A fence labeled with a
# programming language never counts, since "->" and "=>" in real code would
# otherwise pass the flow check.
DIAGRAM_INFO_STRINGS = (
    "", "text", "txt", "plain", "plaintext", "ascii", "diagram", "flow", "none",
    "nohighlight", "raw", "output",
)

# Mermaid renders as raw source in the terminal, so a fence tagged "mermaid",
# or whose first line starts with one of these keywords, fails both diagram
# modes even though its "-->" arrows would otherwise count.
MERMAID_KEYWORDS = (
    "graph", "flowchart", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram",
    "block-beta", "gantt", "mindmap",
)

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
        "Present the reply as a flow diagram drawn in plain text inside a fenced code block: "
        "at least %d steps or decisions as labels or boxes, joined by arrows (`%s`, `%s`, "
        "`-->`) in the order things happen. Not Mermaid: the terminal shows raw source. One "
        "caption line outside the block is fine."
        % (FLOW_MIN_STEPS, FLOW_ARROW_GLYPHS[0], FLOW_ARROW_GLYPHS[1])
    ),
    "block": (
        "Present the reply as a block diagram in plain text inside a fenced code block: "
        "%d or more labeled boxes (`%s─┐ │ │ └─┘` or `+--+`) with lines or arrows showing "
        "how they connect. Not Mermaid: the terminal shows raw source. One caption line "
        "outside the block is fine." % (BLOCK_MIN_BOXES, BOX_CORNERS[0])
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
