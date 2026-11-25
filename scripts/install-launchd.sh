#!/usr/bin/env bash
set -euo pipefail

CONFIG="${CLAUDE_SLACK_CONFIG:-$HOME/.claude-slack/config.env}"
. "$CONFIG"
: "${CLAUDE_SLACK_APP_ID:?set CLAUDE_SLACK_APP_ID in $CONFIG}"
LABEL="${CLAUDE_SLACK_LABEL:-com.claude-slack.bridge}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
SUBS_DIR="${CLAUDE_SLACK_SUBS_DIR:-$HOME/.claude-slack/subs}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$DIR/logs" "$SUBS_DIR" "$(dirname "$PLIST")"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/.slack/bin/slack</string>
    <string>run</string>
    <string>--app=$CLAUDE_SLACK_APP_ID</string>
    <string>--manifest-source=local</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>$DIR/.venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>CLAUDE_SLACK_SUBS_DIR</key><string>$SUBS_DIR</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$DIR/logs/bridge.log</string>
  <key>StandardErrorPath</key><string>$DIR/logs/bridge.log</string>
</dict>
</plist>
PLIST
plutil -lint "$PLIST" >/dev/null
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
for _ in $(seq 1 20); do
  launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || break
  sleep 0.5
done
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "loaded $LABEL; log: $DIR/logs/bridge.log"
