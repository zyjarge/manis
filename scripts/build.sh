#!/usr/bin/env bash
# Build manis.app locally and smoke-test the result.
#
# This is the **developer convenience** wrapper — it builds AND verifies
# the bundle launches. For CI / multi-platform releases, see
# scripts/build-{mac,windows,linux}.sh instead.
#
# Usage:
#     ./scripts/build.sh
#
# Requires:
#     - macOS (PyInstaller BUNDLE target is darwin-only)
#     - brew install python@3.13   (a framework build of Python 3.13)
#     - uv (https://docs.astral.sh/uv/)
#
# Smoke test: launches the .app, waits 3s, confirms the process is alive,
# then kills it. Catches the most common regression (the bundle crashing
# on launch because the Python runtime can't be located).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/build-mac.sh"

APP_NAME="manis"
APP_PATH="dist/${APP_NAME}.app"

echo
echo "▶ Smoke-testing $APP_PATH"
open "$APP_PATH"
sleep 3
PID=$(pgrep -f "${APP_NAME}.app/Contents/MacOS/${APP_NAME}" || true)
if [[ -z "$PID" ]]; then
    echo "❌  $APP_NAME exited within 3s of launch — check Console.app for crash log." >&2
    exit 1
fi
echo "✅  $APP_NAME running (pid $PID) — killing it"
kill "$PID" 2>/dev/null || true

echo
echo "✅  Done. Bundle:  $APP_PATH"
echo "   Open with:    open $APP_PATH"