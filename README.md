# claude-fmt

[![tests](https://github.com/inder/claude-fmt/actions/workflows/tests.yml/badge.svg)](https://github.com/inder/claude-fmt/actions/workflows/tests.yml)

A Claude Code plugin that keeps every reply in the format you choose. Pick a mode once with
`/fmt:mode` and it applies to every reply after that, in every session, until you change it.

| Mode | What you get | Checked? |
| --- | --- | --- |
| `concise` | The answer first, in about 120 words | yes |
| `elaborate` | Step-by-step reasoning, details, trade-offs, examples | no |
| `bulleted` | A bulleted list, not paragraphs | yes |
| `tabular` | One or more Markdown tables | yes |
| `flow` | A text flow diagram (steps joined by arrows) in a code block | yes |
| `block` | A text block diagram (boxes and connections) in a code block | yes |
| `custom "<instruction>"` | Your own formatting instruction, applied every time | no |
| `original` | No change: the plugin does nothing | n/a |

## Install

From GitHub, inside Claude Code:

```
/plugin marketplace add inder/claude-fmt
/plugin install fmt@claude-fmt
```

Or from a shell, the same two steps with the CLI (`--scope local` limits it to the current project):

```bash
claude plugin marketplace add inder/claude-fmt
claude plugin install fmt@claude-fmt
```

From a local clone, use the path instead of `inder/claude-fmt`:

```bash
git clone https://github.com/inder/claude-fmt.git
claude plugin marketplace add ./claude-fmt
claude plugin install fmt@claude-fmt
```

Requires `python3` 3.9 or later on your `PATH`. Works on macOS and Linux.

## Use

```
/fmt:mode tabular                       # every reply as tables from now on
/fmt:mode custom "answer as a haiku"    # your own instruction
/fmt:mode                               # show the current mode
/fmt:mode original                      # turn it off
```

`/fmt:mode` is handled by a hook, so it costs no tokens and never reaches the model. The mode is
saved in `~/.config/claude-fmt/state.json` (or under `$XDG_CONFIG_HOME`), so it carries over to new
sessions.

## How it works

1. **Instruct.** Before each prompt reaches Claude, a hook adds the mode's instruction to the
   context. The instruction covers only the layout of Claude's final reply, not tool calls, files it
   writes, commit messages or code, which stay in normal code blocks.
2. **Check.** When Claude finishes, a hook checks the final reply's shape against the mode with
   deterministic rules (a table with a separator row, mostly bullet lines, arrows or boxes inside
   a code block, a word limit). Short replies and clarifying questions are left alone.
3. **Send back once.** If the reply missed, the hook asks Claude to reply again with the same answer
   in the right format. You see the first reply, a "Stop hook feedback" line, and the reformatted
   reply below it. There is at most one retry per turn, and the retry is never checked again.

The rules lean toward passing: a reply that is close enough is not sent back. `elaborate` and
`custom` are instructed but not checked, because there is no fixed shape to check.

## Limits

- **Final reply only.** Short notes Claude writes between tool calls, and subagents' output, are
  not reformatted.
- **Diagrams are plain text.** The terminal shows Mermaid as raw source, so Mermaid doesn't count.
- **One global mode.** The mode applies to every Claude Code session on the machine, including
  scripted `claude -p` runs. For a script that parses Claude's output, set `CLAUDE_FMT_OFF=1` in its
  environment and the plugin does nothing for that run.
- **A request in the message can win.** If you set a mode and then ask for another format in a
  message ("in two paragraphs, please"), Claude sometimes keeps what you asked for in that message.
- **A retry makes the turn longer.** In `concise` mode, a reply that was too long is followed by
  the short version, so the turn as a whole gets longer, not shorter.
- **Windows is not supported.**

## Command line

`bin/claude-fmt` shows or sets the mode from a shell (it is on the `PATH` of Claude's Bash tool
while the plugin is enabled):

```bash
claude-fmt mode bulleted
claude-fmt get
claude-fmt reset
claude-fmt path
```

## Development

```bash
python3 -m unittest discover -s tests
```

The shape checker is tested against a corpus of real Claude replies (`tests/corpus/captured/`),
labeled by an independent grader that never saw the checker. The corpus also holds hand-made
near-misses that must fail and short valid replies that must pass. CI runs the whole suite on
Ubuntu and macOS with Python 3.9 and 3.12.

`tests/live/` runs the plugin against real Claude, including a scripted terminal session. These
checks need a logged-in Claude Code and cost money; see `tests/live/README.md`.

## License

MIT
