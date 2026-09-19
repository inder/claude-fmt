# Grading rubric for captured replies

Captured replies in `../captured/` were labeled by an independent grader (Claude Sonnet, run as a
separate agent) that saw only the replies and this rubric, never the checker's code. Its raw
output is in `grader-*.json`; `manifest.json` turns YES/NO into pass/fail, omits BORDERLINE, and
moves disagreements the checker accepts on purpose into `known_false_pass`.

The grader was asked to judge layout only, strictly and literally, and to grade every reply
against every format (a reply can satisfy several):

- **concise**: the reply is short and direct, roughly 200 words of prose or fewer (code blocks
  don't count), no padding.
- **bulleted**: the reply's content is mostly bullet points (at least ~60% of its prose lines are
  bullets or numbered items), not paragraphs. Table rows, headings and code blocks don't count.
- **tabular**: the reply is mainly one or more real Markdown tables written directly in the reply
  (header row, separator row, rows), not inside a code block, with at most a little prose around
  them.
- **flow**: the reply contains a plain-text flow diagram inside a fenced code block, steps joined
  by arrows in order. Mermaid source does not count; arrows inside real program code do not count.
- **block**: the reply contains a plain-text block diagram inside a fenced code block, two or more
  drawn boxes connected by lines or arrows. Mermaid does not count.

Answers were YES, NO or BORDERLINE (with a short reason).
