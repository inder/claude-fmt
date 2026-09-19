# Grader prompts, verbatim

The exact prompts given to the independent grader (Claude Sonnet, run as a separate agent) that labeled
`../captured/`. Local file paths are replaced with `<out>`, `<out2>` and `<labels>`.

## Batch 1 (`grader-batch1.json`, the first 24 captures)

> You are labeling Claude replies for whether they follow a requested OUTPUT FORMAT. Judge only layout,
> not content quality. Do not look for or read any checker/source code — judge by the rubric below only.
>
> Directory: `<out>`
> Files are named `<mode>-<question>-<model>.md` (ignore the .err files). For EVERY .md file (24 total), grade it
> against EACH of these five formats (so 24 × 5 = 120 judgments):
>
> - concise: the reply is short and direct — roughly 200 words of prose or fewer (code blocks don't count), no padding.
> - bulleted: the reply's content is mostly bullet points (at least ~60% of its prose lines are bullets or numbered
>   items); not paragraphs.
> - tabular: the reply is mainly one or more real Markdown tables written directly in the reply (header row +
>   separator row + rows), NOT inside a code block, with at most a little prose around them.
> - flow: the reply contains a plain-text flow diagram inside a fenced code block — steps joined by arrows in order.
>   Mermaid source does NOT count.
> - block: the reply contains a plain-text block diagram inside a fenced code block — two or more drawn boxes
>   connected by lines/arrows. Mermaid does NOT count.
>
> Rules: a reply can satisfy several formats. Be strict and literal: if a format's defining feature is absent, it's
> NO. If genuinely borderline, say BORDERLINE with a 6-word reason.
>
> Write your results as JSON to `<labels>` in the form:
> `{"<file-stem>": {"concise": "YES|NO|BORDERLINE", "bulleted": ..., "tabular": ..., "flow": ..., "block": ..., "notes": "<≤15 words, only if something is borderline>"}, ...}`
> Then reply with just the file path and a count of YES/NO/BORDERLINE per format.

## Relabel of one re-captured reply (`bulleted-q3-opus`, recorded in `grader-batch1.json`)

> Label ONE Claude reply for whether it follows each of five OUTPUT FORMATS. Judge layout only. Do not look at any
> checker or source code.
>
> File: `<out>/recap-bulleted-q3-opus.md`
>
> Rubric:
> - concise: short and direct — roughly 200 words of prose or fewer (code blocks don't count).
> - bulleted: content is mostly bullet points (at least ~60% of prose lines are bullets or numbered items), not
>   paragraphs. Table rows and headings don't count toward the total.
> - tabular: mainly one or more real Markdown tables written directly in the reply (header + separator + rows), NOT
>   inside a code block, with little prose around them.
> - flow: contains a plain-text flow diagram inside a fenced code block — steps joined by arrows. Mermaid doesn't count.
> - block: contains a plain-text block diagram inside a fenced code block — two or more drawn boxes connected by
>   lines/arrows. Mermaid doesn't count.
>
> Be strict and literal; say BORDERLINE with a 6-word reason only if genuinely unclear. Reply with exactly one JSON
> object: `{"concise": "YES|NO|BORDERLINE", "bulleted": ..., "tabular": ..., "flow": ..., "block": ..., "notes": "..."}`

## Batch 2 (`grader-batch2.json`, the five code-heavy captures)

> You are labeling Claude replies for whether they follow a requested OUTPUT FORMAT. Judge only layout, not content
> quality. Do not look for or read any checker/source code — judge by the rubric below only.
>
> Directory: `<out2>`
> Grade EVERY .md file (5 files; ignore .err) against EACH of these five formats:
>
> - concise: the reply is short and direct — roughly 200 words of prose or fewer (code blocks don't count), no padding.
> - bulleted: the reply's content is mostly bullet points (at least ~60% of its prose lines are bullets or numbered
>   items); not paragraphs. Table rows, headings and code blocks don't count toward the total.
> - tabular: the reply is mainly one or more real Markdown tables written directly in the reply (header row +
>   separator row + rows), NOT inside a code block, with at most a little prose around them. Code blocks alongside
>   are fine.
> - flow: the reply contains a plain-text flow diagram inside a fenced code block — steps joined by arrows in order.
>   Mermaid source does NOT count; arrows inside real program code do NOT count.
> - block: the reply contains a plain-text block diagram inside a fenced code block — two or more drawn boxes
>   connected by lines/arrows. Mermaid does NOT count.
>
> Rules: a reply can satisfy several formats. Be strict and literal: if a format's defining feature is absent, it's
> NO. If genuinely borderline, say BORDERLINE with a 6-word reason. A very short reply (a sentence or two plus code)
> should still be judged literally per format.
>
> Write JSON to `<labels>`: `{"<file-stem>": {"concise": "YES|NO|BORDERLINE", "bulleted": ..., "tabular": ..., "flow": ..., "block": ..., "notes": "<≤15 words, only if borderline>"}, ...}`
> Reply with just the path and per-format YES/NO/BORDERLINE counts.
