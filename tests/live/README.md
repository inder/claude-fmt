# Live checks

These scripts run the plugin against real Claude replies. They need a logged-in Claude Code, cost
money (roughly 50 model calls for a full harness run), and are not part of CI. The unit tests and
the checker's corpus meta-test (`python3 -m unittest discover -s tests`) run in CI.

Results are written to `tests/live/results/` (ignored by git).

## harness.py: headless

```bash
python3 tests/live/harness.py            # sonnet, plus opus for two modes
```

For each checked mode it runs a natural question, the same question with a request for two
paragraphs of prose, and a forced miss with injection switched off (`CLAUDE_FMT_NO_INJECT=1`), so
the Stop hook has to rescue the reply. It also runs `original`. Every final reply is graded by the
plugin's own checker and by an independent judge: a separate Claude call that sees only the
reply and the rubric in `tests/corpus/labels/rubric.md`, never the checker. Before anything runs,
the judge is calibrated on a known-bad and a known-good reply per mode, and the run aborts if it
misgrades either.

Each run's hooks write their decisions to a trace file (`CLAUDE_FMT_TRACE`), so the harness checks
what the hooks actually did. For example, under `original` neither hook produced output, and after a
send-back the continuation's Stop is marked as a retry and stays silent.

## interactive.py: a real terminal session

```bash
brew install tmux                        # or your package manager
python3 tests/live/interactive.py                          # install from this checkout
python3 tests/live/interactive.py --source inder/claude-fmt   # install from GitHub
```

It drives Claude Code through tmux in a scratch project. It adds the marketplace with
`claude plugin marketplace add --scope local`, then installs through the in-session `/plugin`
menu, choosing local scope. It then sets each mode with `/fmt:mode`, asks a question and grades the reply.
It also checks `original`, checks that a mode survives into a new session through the default state
path, and forces a miss to see the appended fix and the "Stop hook feedback" line on screen.

Everything it installs is scoped to the scratch project. It fingerprints `~/.claude/settings.json`
and `~/.config/claude-fmt/state.json` before and after, and always uninstalls and removes the
scratch project, even when a step fails.
