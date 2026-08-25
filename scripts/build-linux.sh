#!/usr/bin/env bash
# Build manis on Linux and package it as a .tar.gz.
#
# Usage:
#     PYTHON_BIN=/usr/bin/python3.13 ./scripts/build-linux.sh
#
# Outputs:
#     dist/manis-{version}-linux-x86_64.tar.gz  (containing dist/manis/ binary + README)
#
# Notes:
#   - PyInstaller on Linux produces dist/manis/manis (a folder bundle
#     with .so libraries). We tar.gz the whole dist/manis/ directory.
#   - pywebview on Linux uses GTK WebKit. The resulting binary will
#     refuse to launch on a headless machine — install
#     `libwebkit2gtk-4.1-0` etc. on the runner if you want to smoke-test.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
BUILD_LABEL="Linux"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=build-common.sh
source "$SCRIPT_DIR/build-common.sh"

if [[ ! -f "dist/manis/manis" ]]; then
    echo "❌  Build failed — dist/manis/manis not produced." >&2
    ls -la dist/ >&2 || true
    exit 1
fi

VERSION="$(grep -E '^version\s*=' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/')"
ARCH="$(uname -m)"
ARTIFACT_BASE="manis-${VERSION}-linux-${ARCH}"

cd dist
echo "▶ Packaging → ${ARTIFACT_BASE}.tar.gz"
rm -f "${ARTIFACT_BASE}.tar.gz"
tar -czf "${ARTIFACT_BASE}.tar.gz" ./manis
cd ..

echo "✅  Linux artifact:"
ls -lh "dist/${ARTIFACT_BASE}.tar.gz"