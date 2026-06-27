#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.televera.local.plist"
PYTHON_BIN="$(command -v python3)"

mkdir -p "$PLIST_DIR" "$ROOT_DIR/logs"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.televera.local</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-lc</string>
    <string>cd "$ROOT_DIR" &amp;&amp; mkdir -p logs data &amp;&amp; "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &amp; BACKEND_PID=\$!; npm run dev -- --host 127.0.0.1 --port 8080 --strictPort &amp; FRONTEND_PID=\$!; trap 'kill \$BACKEND_PID \$FRONTEND_PID 2&gt;/dev/null' EXIT INT TERM; wait</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$ROOT_DIR/logs/local-launchagent.out.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT_DIR/logs/local-launchagent.err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/anaconda3/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/com.televera.local"

echo "Installed Televera local autostart."
echo "Frontend: http://localhost:8080"
echo "Backend:  http://localhost:8000"
