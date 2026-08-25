#!/usr/bin/env bash
# Build manis.exe on Windows and package it as a .zip.
#
# Usage (from a Windows runner / Git Bash):
#     PYTHON_BIN=/c/Python313/python.exe ./scripts/build-windows.sh
#
# Outputs:
#     dist/manis-{version}-windows.zip  (containing dist/manis/ + README)
#
# Notes:
#   - PyInstaller on Windows produces dist/manis/manis.exe (a folder
#     bundle with DLLs), so we zip the whole dist/manis/ directory.
#   - Requires Python 3.10+ (3.13 works fine on Windows) — does NOT
#     need to be a "framework" build (Windows has no such concept).
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
BUILD_LABEL="Windows"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=build-common.sh
source "$SCRIPT_DIR/build-common.sh"

# PyInstaller's spec produces dist/manis/manis.exe on Windows
if [[ ! -f "dist/manis/manis.exe" ]]; then
    echo "❌  Build failed — dist/manis/manis.exe not produced." >&2
    echo "   Did PyInstaller create the bundle? Listing dist/:" >&2
    ls -la dist/ >&2 || true
    exit 1
fi

# Version comes from pyproject.toml (no PlistBuddy on Windows)
VERSION="$(grep -E '^version\s*=' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/')"
ARTIFACT_BASE="manis-${VERSION}-windows"

cd dist
# Zip the folder bundle. `-r` recurses, `-q` quiet, archive format determined by filename.
if command -v 7z >/dev/null 2>&1; then
    echo "▶ Packaging with 7z → ${ARTIFACT_BASE}.zip"
    rm -f "${ARTIFACT_BASE}.zip"
    7z a -tzip -mx=9 "${ARTIFACT_BASE}.zip" ./manis >/dev/null
elif command -v zip >/dev/null 2>&1; then
    echo "▶ Packaging with zip → ${ARTIFACT_BASE}.zip"
    rm -f "${ARTIFACT_BASE}.zip"
    zip -r -q -9 "${ARTIFACT_BASE}.zip" ./manis
else
    echo "❌  Neither zip nor 7z found on PATH" >&2
    exit 1
fi
cd ..

echo "✅  Windows artifact:"
ls -lh "dist/${ARTIFACT_BASE}.zip"