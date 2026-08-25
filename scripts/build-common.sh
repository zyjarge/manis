#!/usr/bin/env bash
# Shared PyInstaller build logic, sourced by platform-specific scripts.
#
# Sets up the venv (with framework Python on macOS), installs deps,
# and runs `pyinstaller manis.spec`. Does NOT package the result into
# an installable artifact — that's the caller's job (see build-{mac,windows,linux}.sh).
#
# Required env vars from caller:
#   PYTHON_BIN    absolute path to a working Python interpreter
#   BUILD_LABEL   e.g. "macOS" — used for logging only
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

: "${PYTHON_BIN:?PYTHON_BIN must be set}"
: "${BUILD_LABEL:?BUILD_LABEL must be set}"

if [[ ! -e "$PYTHON_BIN" ]]; then
    # On Windows the binary path ends in '.exe' so [[ -x ]] misses it
    if [[ ! -e "${PYTHON_BIN}.exe" ]]; then
        echo "❌  Python interpreter not found: $PYTHON_BIN" >&2
        exit 1
    fi
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "❌  uv not found. Install:  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

echo "▶ [$BUILD_LABEL] Recreating .venv with $PYTHON_BIN"
rm -rf .venv
UV_PYTHON="$PYTHON_BIN" uv venv --python "$PYTHON_BIN"

echo "▶ [$BUILD_LABEL] Installing dependencies"
UV_PYTHON="$PYTHON_BIN" uv sync

# Install pyinstaller into the venv. Use `uv pip install` (not `uv add`)
# because pyinstaller is a build-only tool, not a runtime dependency.
# `--python .venv` is portable across macOS/Linux (.venv/bin/python)
# and Windows (.venv/Scripts/python.exe) — uv resolves it.
UV_PYTHON="$PYTHON_BIN" uv pip install --python .venv pyinstaller

echo "▶ [$BUILD_LABEL] Cleaning build/ and dist/"
rm -rf build dist

echo "▶ [$BUILD_LABEL] Running PyInstaller"
# `uv run` resolves the right python.exe on Windows automatically.
UV_PYTHON="$PYTHON_BIN" uv run --python .venv pyinstaller --noconfirm manis.spec