#!/usr/bin/env bash
# Build manis.app with PyInstaller.
#
# Usage:
#     ./scripts/build.sh
#
# Requires:
#     - macOS (PyInstaller BUNDLE target is darwin-only)
#     - brew install python@3.13   (a framework build of Python 3.13)
#     - uv (https://docs.astral.sh/uv/)
#
# What it does:
#     1. Re-creates .venv using the framework build of Python 3.13 (so the
#        bundled libpython can be located at runtime — non-framework builds
#        produce "A Python runtime could not be located" on launch).
#     2. Installs project deps + PyInstaller into the venv.
#     3. Wipes any stale build/dist so the output is reproducible.
#     4. Runs `pyinstaller manis.spec`.
#     5. Smoke-tests the bundle by launching it and confirming the process
#        stays alive for a few seconds.
set -euo pipefail

# ---------------------------------------------------------------------------
# Configurable bits — override on the command line if needed:
#   PYTHON_BIN=/path/to/python3.13 ./scripts/build.sh
# ---------------------------------------------------------------------------
PYTHON_BIN="${PYTHON_BIN:-/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13}"
APP_NAME="manis"
SPEC="${APP_NAME}.spec"

cd "$(dirname "$0")/.."

# Sanity checks ----------------------------------------------------------
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌  PyInstaller BUNDLE target is macOS-only (you're on $(uname))." >&2
    exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "❌  Python interpreter not found: $PYTHON_BIN" >&2
    echo "   Install with:  brew install python@3.13" >&2
    echo "   Or set PYTHON_BIN to a framework build of Python 3.13." >&2
    exit 1
fi

if ! "$PYTHON_BIN" -c "import sys, sysconfig; sys.exit(0 if sysconfig.get_config_var('PYTHONFRAMEWORK') == 'Python' else 1)"; then
    echo "❌  $PYTHON_BIN is not a framework build." >&2
    echo "   Only framework builds bundle correctly into .app." >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "❌  uv not found. Install:  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Build the venv (force the framework interpreter, overriding .python-version)
# ---------------------------------------------------------------------------
echo "▶ Re-creating .venv with $PYTHON_BIN"
rm -rf .venv
UV_PYTHON="$PYTHON_BIN" uv venv --python "$PYTHON_BIN"

# ---------------------------------------------------------------------------
# 2. Install deps
# ---------------------------------------------------------------------------
echo "▶ Installing dependencies"
UV_PYTHON="$PYTHON_BIN" uv sync
UV_PYTHON="$PYTHON_BIN" uv pip install --python .venv/bin/python pyinstaller

# ---------------------------------------------------------------------------
# 3. Wipe stale build output
# ---------------------------------------------------------------------------
echo "▶ Cleaning build/ and dist/"
rm -rf build dist

# ---------------------------------------------------------------------------
# 4. Run PyInstaller
# ---------------------------------------------------------------------------
echo "▶ Running PyInstaller ($SPEC)"
UV_PYTHON="$PYTHON_BIN" .venv/bin/pyinstaller --noconfirm "$SPEC"

APP_PATH="dist/${APP_NAME}.app"
if [[ ! -d "$APP_PATH" ]]; then
    echo "❌  Build failed — $APP_PATH not produced." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 5. Smoke-test (launch + verify the process is alive a couple seconds later)
# ---------------------------------------------------------------------------
echo "▶ Smoke-testing $APP_PATH"
open "$APP_PATH"
sleep 3
PID_FILE="$APP_PATH/Contents/MacOS/$APP_NAME"
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