# AGENTS.md

Guidance for coding agents working in this repository. User-facing docs: [README.md](README.md).

## What This Is

A Slack event bridge for Claude Code sessions: `bridge.py` fans Slack message events out to subscriber files in `~/.claude-slack/subs/`; `app.py` starts Bolt in Socket Mode. The Claude Code plugin is in `plugins/slack-bridge/` (marketplace: `.claude-plugin/marketplace.json`). No LLM and no rules in the bridge: filtering belongs to each subscription.

Local settings (app ID, owner user ID, paths, launchd label) live in `~/.claude-slack/config.env`, never in this repo. Do not commit workspace, channel or user IDs.

## Running

- The bridge runs as a launchd agent made by `scripts/install-launchd.sh` (label from the config). Log: `logs/bridge.log`.
- Restart after changing `bridge.py` is not needed: `slack run` reloads on file changes. Restart with `launchctl kickstart -k gui/$(id -u)/<label>`.
- Do not also run `slack run` by hand while the agent runs: two Socket Mode connections split the events.
- `manifest.json` is pushed to the app on every start (`--manifest-source=local`). Edit it here, not in App Settings.
- After editing the plugin: `claude plugin marketplace update claude-slack && claude plugin update slack-bridge@claude-slack`.

## Before You Finish

Run `.venv/bin/python bridge.py` (self-check), `uvx ruff check . && uvx ruff format --check .`, and `bash -n` on the shell scripts.

## Code Style

- Snake-case filenames
- No code comments. Make the code explain itself with clear names, tests, or types.
