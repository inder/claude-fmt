"""Deterministic shape checks for the fmt plugin's output modes.

check(mode, text) returns (ok, reason). It judges the layout of Claude's
final reply against the mode the user chose. Every rule leans toward passing:
a false fail makes the Stop hook send a correct reply back, which the user
sees as a duplicate, while a false pass costs only a missed reformat. The one
exception is Mermaid in a diagram mode, which the terminal shows as raw
source and which is cheap to detect exactly.

All thresholds come from fmt_modes, which also builds the instruction Claude
was given, so the two cannot drift apart.
"""

import math
import re

import fmt_modes as M

CHECKED_MODES = ("concise", "bulleted", "tabular", "flow", "block")

_FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
_HEADING = re.compile(r"^\s{0,3}#{1,6}(\s|$)")
_RULE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
_BULLET = re.compile(r"^\s*([-*+•]|\d{1,3}[.)])\s+\S")
_SEPARATOR = re.compile(M.TABLE_SEPARATOR_RE)
_ARROW = re.compile(
    "[-=─═━]+>|<[-=─═━]+|["
    + "".join(M.FLOW_ARROW_GLYPHS)
    + "⇒⇨◀▲◄]"
)
_DOWN_ARROWS = re.compile(r"^\s*(?:[vV^]\s*)+$")
_ASCII_BORDER = re.compile(r"\+(?=-{2,}\+)")
_MERMAID_FIRST_LINE = re.compile(r"^\s*(%s)\b" % "|".join(re.escape(k) for k in M.MERMAID_KEYWORDS))
_WORD = re.compile(r"[^\W_]", re.UNICODE)


class _Fence(object):
    def __init__(self, info, lines):
        self.info = info
        self.lines = lines
        words = info.split()
        self.info_word = words[0].lower() if words else ""

    @property
    def is_mermaid(self):
        if self.info_word == "mermaid":
            return True
        for line in self.lines:
            if line.strip():
                return bool(_MERMAID_FIRST_LINE.match(line))
        return False

    @property
    def can_be_diagram(self):
        return self.info_word in M.DIAGRAM_INFO_STRINGS and not self.is_mermaid


def split_blocks(text):
    """Split a reply into prose lines and fenced code blocks.

    Prose is returned as a list in which None marks where a fence was, so two
    prose lines on either side of a fence are never treated as adjacent. A
    fence may be indented (it can sit under a nested bullet), and an unclosed
    fence runs to the end of the reply.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    prose, fences = [], []
    current = None  # (fence char, fence length, info, body lines)
    for line in lines:
        if current is None:
            match = _FENCE_OPEN.match(line)
            if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
                current = (match.group(1)[0], len(match.group(1)), match.group(2).strip(), [])
                prose.append(None)
            else:
                prose.append(line)
            continue
        char, length, info, body = current
        stripped = line.strip()
        if stripped and set(stripped) == {char} and len(stripped) >= length:
            fences.append(_Fence(info, body))
            current = None
        else:
            body.append(line)
    if current is not None:
        fences.append(_Fence(current[2], current[3]))
    return prose, fences


def count_words(lines):
    return sum(
        1 for line in lines if line is not None for token in line.split() if _WORD.search(token)
    )


def _cells(line):
    return [cell for cell in line.strip().strip("|").split("|")]


def find_tables(prose):
    """Return the indexes of prose lines that belong to Markdown tables.

    A table is a line with at least two cells, then a separator row, then at
    least one body row, all containing "|".
    """
    in_table = set()
    for i, line in enumerate(prose):
        if line is None or not _SEPARATOR.match(line):
            continue
        if i == 0 or i + 1 >= len(prose):
            continue
        header, body = prose[i - 1], prose[i + 1]
        if header is None or body is None or "|" not in header or "|" not in body:
            continue
        if len(_cells(header)) < 2:
            continue
        in_table.update((i - 1, i))
        j = i + 1
        while j < len(prose) and prose[j] is not None and "|" in prose[j] and prose[j].strip():
            in_table.add(j)
            j += 1
    return in_table


def count_arrows(lines):
    total = 0
    for line in lines:
        if _DOWN_ARROWS.match(line):
            total += len(line.split())
        else:
            total += len(_ARROW.findall(line))
    return total


def count_boxes(lines):
    unicode_boxes = sum(
        1 for line in lines for ch in line if ch in M.BOX_CORNERS or ch in M.BOX_TEES
    )
    segments = sum(len(_ASCII_BORDER.findall(line)) for line in lines)
    return max(unicode_boxes, int(math.ceil(segments / 2.0)))


def _check_tabular(prose, fences):
    tables = find_tables(prose)
    if not tables:
        in_fence = any(find_tables(list(fence.lines)) for fence in fences)
        if in_fence:
            return False, "the table is inside a code block, where it shows as raw text"
        return False, "no Markdown table (a header row, a separator row, then rows)"
    table_words = count_words(prose[i] for i in sorted(tables) if not _SEPARATOR.match(prose[i]))
    outside = count_words(line for i, line in enumerate(prose) if i not in tables)
    if outside > M.TABULAR_MAX_PROSE_WORDS and outside > table_words:
        return False, "%d words of prose outside the tables, more than the tables hold" % outside
    return True, "table"


def _check_bulleted(prose):
    tables = find_tables(prose)
    content = [
        line
        for i, line in enumerate(prose)
        if line is not None
        and line.strip()
        and i not in tables
        and not _HEADING.match(line)
        and not _RULE.match(line)
    ]
    if not content:
        return False, "no bullet points"
    bullets = sum(1 for line in content if _BULLET.match(line))
    ratio = bullets / float(len(content))
    if ratio < M.BULLET_RATIO:
        return False, "only %d%% of lines are bullets (needs %d%%)" % (
            round(ratio * 100),
            round(M.BULLET_RATIO * 100),
        )
    return True, "bulleted"


def _check_diagram(mode, prose, fences):
    capable = [fence for fence in fences if fence.can_be_diagram]
    if mode == "flow":
        needed = M.FLOW_MIN_STEPS - 1
        best = max([count_arrows(fence.lines) for fence in capable] or [0])
        if best >= needed:
            return True, "flow diagram"
        shortfall = "no text diagram with at least %d arrows in a code block" % needed
    else:
        needed = M.BLOCK_MIN_BOXES
        best = max([count_boxes(fence.lines) for fence in capable] or [0])
        if best >= needed:
            return True, "block diagram"
        shortfall = "no text diagram with at least %d boxes in a code block" % needed
    if any(fence.is_mermaid for fence in fences):
        return False, "the diagram is Mermaid, which the terminal shows as raw source"
    if count_words(prose) < M.SHORT_REPLY_WORDS:
        return True, "short reply"
    return False, shortfall


def check(mode, text):
    """Return (ok, reason) for whether `text` has the shape `mode` asks for."""
    try:
        if mode not in CHECKED_MODES or not isinstance(text, str):
            return True, "not checked"
        prose, fences = split_blocks(text)
        if mode in ("flow", "block"):
            return _check_diagram(mode, prose, fences)
        prose_words = count_words(prose)
        if prose_words < M.SHORT_REPLY_WORDS:
            return True, "short reply"
        if mode == "concise":
            if prose_words > M.CONCISE_MAX_WORDS:
                return False, "%d words of prose (limit %d)" % (prose_words, M.CONCISE_MAX_WORDS)
            return True, "concise"
        if mode == "tabular":
            return _check_tabular(prose, fences)
        return _check_bulleted(prose)
    except Exception as err:  # never let a checker bug reach the user
        return True, "checker error: %s" % err
