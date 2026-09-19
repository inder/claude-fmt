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

"Checked" modes are also verified after each reply, and a reply in the wrong shape is sent back
once to be reformatted (see [How it works](#how-it-works)).

## One-line install

Paste this into Claude Code:

```
Install the claude-fmt plugin for me: run `claude plugin marketplace add inder/claude-fmt` and then `claude plugin install fmt@claude-fmt`, and tell me when it's done.
```

Or run it yourself in a terminal:

```bash
claude plugin marketplace add inder/claude-fmt && claude plugin install fmt@claude-fmt
```

Both install it for your user account (every project). Then start a new Claude Code session and run
`/fmt:mode` to pick a mode.

## Quick start

1. Install it, inside Claude Code:

   ```
   /plugin marketplace add inder/claude-fmt
   /plugin install fmt@claude-fmt
   ```

   When `/plugin install` asks where to install, pick **Install for you (user scope)** to use it
   everywhere, or **Install for you, in this repo only (local scope)** to try it in one project.

2. Pick a mode:

   ```
   /fmt:mode tabular
   ```

   You see `fmt: mode → tabular`. Nothing is sent to Claude.

3. Ask anything as usual. The reply comes back as tables:

   ```
   > Compare PostgreSQL and SQLite for a small web app.

   | Aspect     | SQLite                      | PostgreSQL                        |
   | ---------- | --------------------------- | --------------------------------- |
   | Setup      | No server, one file on disk | A server to run and back up       |
   | Writes     | One writer at a time        | Many concurrent writers           |
   | Best for   | One machine, modest traffic | Several app servers, growing data |
   ```

4. Switch it off when you're done:

   ```
   /fmt:mode original
   ```

## Using it

```
/fmt:mode                               # show the current mode and the list of modes
/fmt:mode concise                       # short answers
/fmt:mode elaborate                     # detailed answers
/fmt:mode bulleted                      # bulleted lists
/fmt:mode tabular                       # tables
/fmt:mode flow                          # text flow diagrams
/fmt:mode block                         # text block diagrams
/fmt:mode custom "answer as a haiku"    # your own instruction (quotes optional)
/fmt:mode original                      # back to normal: the plugin does nothing
```

- **Mode names are case-insensitive.** An unknown mode, or extra words after a mode that takes none,
  shows an error and leaves the current mode unchanged. A custom instruction can be up to 2,000
  characters.
- **The mode applies everywhere.** It covers every session and every project where the plugin is
  installed, including sessions you start later. It is saved in
  `~/.config/claude-fmt/state.json` (or `$XDG_CONFIG_HOME/claude-fmt/state.json`).
- **Only Claude's final reply is formatted.** Tool calls, files it writes, commit messages and code
  are left alone. Code and command output stay in normal code blocks inside a formatted reply.
- **Short replies are left alone.** A one-line acknowledgement stays plain, and so does a short
  clarifying question Claude asks you.

What the diagram modes look like. `flow`:

```
┌─────────────┐
│ Resolve DNS │
└──────┬──────┘
       ↓
┌──────┴──────┐
│TLS handshake│
└──────┬──────┘
       ↓
 Encrypted HTTP
```

`block`:

```
┌─────────┐      ┌─────────┐      ┌──────────┐
│ Browser │─────▶│   API   │─────▶│ Database │
└─────────┘      └─────────┘      └──────────┘
```

Diagrams are drawn with text characters, because the terminal shows Mermaid as raw source.

## How it works

1. **Instruct.** Before each prompt reaches Claude, a hook adds the mode's instruction to the context.
   It is 130–165 words, added to every prompt while a mode is set, and covers only the layout of the
   final reply.
2. **Check.** When Claude finishes, a hook checks the final reply's shape against the mode with
   deterministic rules: a table with a separator row, mostly bullet lines, arrows or boxes inside a
   code block, or a word limit. The rules lean toward passing: a reply that is close enough is not
   sent back.
3. **Send back once.** If the reply missed, the hook asks Claude to reply again with the same answer in
   the right format. You see the first reply, a `Stop hook feedback` line, and then the reformatted
   reply. There is at most one retry per turn, and the retry is not checked again.

`/fmt:mode` itself is normally handled by a hook before the model sees it, so switching modes costs no
tokens. If that hook doesn't run for some reason, a bundled skill applies the command instead.

`elaborate` and `custom` are instructed but not checked, because they have no fixed shape to check.

## Install options

**In Claude Code** (shown in Quick start): `/plugin marketplace add inder/claude-fmt` registers the
plugin's source for your user account; `/plugin install fmt@claude-fmt` then asks where to install it.

**From a shell** with the `claude` CLI. Without `--scope`, both steps apply to your user account, so
the plugin is active in every project. Add `--scope local` to both commands, run from inside a
project, to keep it to that project.

```bash
claude plugin marketplace add inder/claude-fmt
claude plugin install fmt@claude-fmt
```

**From a local clone**, use the path instead of `inder/claude-fmt`:

```bash
git clone https://github.com/inder/claude-fmt.git
claude plugin marketplace add ./claude-fmt
claude plugin install fmt@claude-fmt
```

Requirements: `python3` 3.9 or later on your `PATH`, on macOS or Linux. On macOS, `python3` comes with
the Xcode Command Line Tools (`xcode-select --install`).

New plugins load when a session starts: start a new session, or run `/reload-plugins`, after
installing.

## Update and uninstall

```bash
claude plugin marketplace update claude-fmt    # fetch the latest version
claude plugin update fmt@claude-fmt            # then restart Claude Code
```

```bash
claude plugin uninstall fmt@claude-fmt         # add --scope local if you installed it that way
claude plugin marketplace remove claude-fmt
rm ~/.config/claude-fmt/state.json             # optional: forget the saved mode
```

The saved mode survives an uninstall, so a reinstall picks up where you left off unless you delete
the file.

## Scripts and automation

The mode also applies to scripted `claude -p` runs. For a script that parses Claude's output, set
`CLAUDE_FMT_OFF=1` in its environment, and the plugin's hooks do nothing for that run:

```bash
CLAUDE_FMT_OFF=1 claude -p "List the files that changed" --output-format json
```

`bin/claude-fmt` shows or sets the mode from a shell. Claude's own Bash tool has it on its `PATH`
while the plugin is enabled. From your own terminal, run it from a clone:

```bash
./claude-fmt/bin/claude-fmt mode bulleted   # same as /fmt:mode bulleted
./claude-fmt/bin/claude-fmt get             # show the current mode
./claude-fmt/bin/claude-fmt reset           # back to original
./claude-fmt/bin/claude-fmt path            # where the mode is saved
```

## Troubleshooting

- **`/fmt:mode` is not recognized.** The plugin isn't loaded in this session. Run `/plugin` and check
  the Installed tab, then start a new session or run `/reload-plugins`.
- **Replies aren't formatted.** Run `/fmt:mode` to check the mode is what you expect (`original` does
  nothing). Check that `python3 --version` works in the shell Claude Code starts from.
- **A hook error mentions python3.** `python3` is missing or is the macOS stub. Install the Xcode
  Command Line Tools or another Python 3.9+.
- **A reply came back twice.** That's the send-back: the first reply missed the format and the
  second is the reformatted one.

## Limits

- **Final reply only.** Short notes Claude writes between tool calls, and subagents' output, are not
  reformatted.
- **Diagrams are plain text.** Mermaid doesn't count.
- **A request in the message can win.** If you set a mode and then ask for another format in a single
  message ("in two paragraphs, please"), Claude sometimes keeps what that message asked for, even
  after the send-back.
- **A retry makes the turn longer.** In `concise` mode, a reply that was too long is followed by the
  short version, so the turn as a whole gets longer, not shorter.
- **Claude Code only.** Codex uses a different plugin format and has no hook that can handle
  `/fmt:mode` before the model sees it, so this plugin does not install there.
- **Windows is not supported.**

## Development

```bash
python3 -m unittest discover -s tests
```

The shape checker is tested against a corpus of real Claude replies (`tests/corpus/captured/`),
labeled by an independent grader that never saw the checker. The corpus also holds hand-made
near-misses that must fail and short valid replies that must pass. CI runs the whole suite on Ubuntu
and macOS with Python 3.9 and 3.12.

`tests/live/` runs the plugin against real Claude, including a scripted terminal session that installs
the plugin, sets each mode and checks the replies. These checks need a logged-in Claude Code and cost
money; see `tests/live/README.md`.

## License

MIT
