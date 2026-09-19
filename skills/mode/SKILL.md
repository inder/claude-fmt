---
name: mode
description: Show or set the output format for every reply (concise, elaborate, bulleted, tabular, flow, block, custom, original).
argument-hint: "[concise|elaborate|bulleted|tabular|flow|block|original|custom \"<instruction>\"]"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/claude-fmt mode *)
---

The fmt plugin's hook normally handles this command before it reaches you. You are reading this
because that hook did not run, so apply the command yourself.

Run this command with the Bash tool, exactly as written:

${CLAUDE_PLUGIN_ROOT}/bin/claude-fmt mode $ARGUMENTS

Then reply with the command's output and nothing else.
