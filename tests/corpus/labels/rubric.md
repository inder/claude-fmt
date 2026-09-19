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
  them. Code blocks alongside the tables (commands, code) are fine and don't count as prose.
- **flow**: the reply contains a plain-text flow diagram inside a fenced code block, steps joined
  by arrows in order. Mermaid source does not count; arrows inside real program code do not count.
- **block**: the reply contains a plain-text block diagram inside a fenced code block, two or more
  drawn boxes connected by lines or arrows. Mermaid does not count.

Answers were YES, NO or BORDERLINE (with a short reason).

The exact grader prompts are in `prompts.md`. They differ slightly: batch 2 told the grader that code
blocks alongside tables are fine, and batch 1 did not. The **tabular** line above includes that sentence.
The first committed version of this file omitted it, and the live judge (which reads this file) then
failed two correct tabular replies: tables carrying the answer, with commands in bash blocks. The
sentence was added because the plugin's own instruction tells Claude to put code and commands in
fenced blocks, so a tabular reply to a how-to question legitimately has them. A table inside a code
block still does not count.
