# claude-slack-bridge: Slack events for Claude Code

**A Claude Code plugin and always-on Slack bot that let Claude Code sessions (AI coding agents) receive Slack messages in real time, without polling.** Follow a Slack thread or channel, wait for a teammate's reply, watch DMs, and reply as a Slack bot, all from a Claude Code session.

The Slack MCP server and Slack plugin can send messages, but reading new ones means polling. This bridge pushes Slack events to the agent instead, so a Claude Code session can act like a team member in Slack.

## How it works

A small always-on Slack app (Bolt for Python, Socket Mode, no public URL needed) receives every message its bot can see. It drops them unless a session subscribes. A session subscribes by naming a file and an optional filter; the bridge appends matching events to that file, one JSON line each, and the session watches it with Claude Code's Monitor tool. Sessions send messages as the bot with the Slack CLI.

```
Slack ──Socket Mode──▶ bridge.py ──match──▶ <session>/events.jsonl ──Monitor──▶ Claude Code session
                                                                                   │
Slack ◀──────────────────── slack-bridge send (chat.postMessage) ◀─────────────────┘
```

Use cases:
- Follow a Slack discussion and act on each new reply (summarize, open a ticket, run a check).
- Ask a question in Slack from a long-running agent task and continue when someone answers.
- Give a Claude Code session a Slack DM inbox.

## Parts

| Path | What |
|---|---|
| `bridge.py`, `app.py` | The bridge: fan-out of Slack message events to subscriber files |
| `manifest.json` | Slack app manifest (bot scopes: `channels:history`, `groups:history`, `im:history`, `chat:write`) |
| `scripts/install-launchd.sh` | Runs the bridge always-on with launchd (macOS) |
| `plugins/slack-bridge/` | Claude Code plugin: skill `slack-events` and the helper `slack-bridge` |
| `config.env.example` | Local settings (app ID, your user ID, paths) |

## Setup

Needs: macOS (for launchd), Python 3.12+, `jq`, the [Slack CLI](https://docs.slack.dev/tools/slack-cli/), Claude Code.

1. Clone and install:
   ```bash
   git clone https://github.com/malay44/claude-slack-bridge.git ~/claude-slack-bridge
   cd ~/claude-slack-bridge
   python3 -m venv .venv && .venv/bin/pip install -e .
   ```
2. Log the Slack CLI in to your workspace: `slack login`.
3. Create the app from this project: `slack run` once (it creates the app from `manifest.json` and installs it), then stop it. Get the app ID with `slack app list`.
4. Write your config:
   ```bash
   mkdir -p ~/.claude-slack && cp config.env.example ~/.claude-slack/config.env
   ```
   Fill in `CLAUDE_SLACK_BRIDGE_DIR`, `CLAUDE_SLACK_APP_ID` and `CLAUDE_SLACK_OWNER` (your Slack user ID: profile > ... > Copy member ID).
5. Start the bridge always-on: `scripts/install-launchd.sh`.
6. Install the plugin:
   ```bash
   claude plugin marketplace add malay44/claude-slack-bridge
   claude plugin install slack-bridge@claude-slack
   ```
7. Invite the bot to the channels it should see: `/invite @claude-slack`.

`slack run` is started with `--manifest-source=local`, so `manifest.json` wins over App Settings on every start.

## Use

In a Claude Code session, ask for it in plain words ("follow this thread and tell me when someone answers"). The `slack-events` skill does the rest. By hand:

```bash
H=plugins/slack-bridge/skills/slack-events/scripts/slack-bridge
$H sub mythread /tmp/mythread.jsonl --match channel=C0123456789 --match thread_ts=1700000000.000100
tail -n 0 -f /tmp/mythread.jsonl          # in Claude Code: Monitor this
$H send C0123456789 "On it." 1700000000.000100
$H unsub mythread
```

Other commands: `list`, `status`, `config`, `thread CHANNEL TS`.

A subscription is a JSON file in `~/.claude-slack/subs/`: `{"out": "...", "match": {...}, "expires_at": "..."}`. `match` is an exact match on event fields (`channel`, `channel_type`, `user`, `thread_ts`, `parent_user_id`, `subtype`, `bot_id`, `ts`, `text`); all keys must match. Without `expires_at` it never expires. The bridge removes a subscription when it expires or when the folder of `out` is gone.

## Limits and safety

- Events that arrive while the bridge is down are lost.
- Event files hold message text from every channel the bot is in. Keep the bot out of channels with sensitive data.
- Only messages from `CLAUDE_SLACK_OWNER` count as your instructions; the skill tells sessions to treat other users' text as untrusted data.

## Keywords

Claude Code plugin, Claude Code Slack integration, Slack bot for AI agents, Slack events API, Slack Socket Mode, Bolt for Python, real-time Slack notifications for agents, Anthropic Claude, agentic workflows, Slack thread follower.

## License

MIT. `app.py` started from Slack's [bolt-python-support-agent](https://github.com/slack-samples/bolt-python-support-agent) sample.
