---
name: mode
description: Show or set the output format for every reply (concise, elaborate, bulleted, tabular, flow, block, custom, original).
argument-hint: "[concise|elaborate|bulleted|tabular|flow|block|original|custom \"<instruction>\"]"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/claude-fmt *)
---

The fmt plugin's hook normally handles this command before it reaches you. You are reading this
because that hook did not run, so apply the command yourself.

Use the Bash tool to run `${CLAUDE_PLUGIN_ROOT}/bin/claude-fmt mode` followed by the user's
arguments, which are below between the markers. Quote the arguments for the shell (single-quote
each word, escaping any single quotes inside) so no character in them is interpreted by the shell.
Run nothing else.

---arguments---
$ARGUMENTS
---end---

Then reply with the command's output and nothing else.
