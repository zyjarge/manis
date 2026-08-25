#!/usr/bin/env bash
# Shared PyInstaller build logic, sourced by platform-specific scripts.
#
# Sets up the venv (with framework Python on macOS), installs deps,
# and runs `pyinstaller manis.spec`. Does NOT package the result into
# an installable artifact — that's the caller's job (see build-{mac,windows,linux}.sh).
#
# Required env vars from caller:
#   PYTHON_BIN    absolute path to a working Python interpreter
#   BUILD_LABEL   e.g. "macOS-x86_64" — used for logging only
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

: "${PYTHON_BIN:?PYTHON_BIN must be set}"
: "${BUILD_LABEL:?BUILD_LABEL must be set}"

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "❌  Python interpreter not found: $PYTHON_BIN" >&2
    exit 1
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
UV_PYTHON="$PYTHON_BIN" uv pip install --python .venv/bin/python pyinstaller

echo "▶ [$BUILD_LABEL] Cleaning build/ and dist/"
rm -rf build dist

echo "▶ [$BUILD_LABEL] Running PyInstaller"
UV_PYTHON="$PYTHON_BIN" .venv/bin/pyinstaller --noconfirm manis.spec