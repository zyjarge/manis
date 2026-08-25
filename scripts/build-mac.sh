#!/usr/bin/env bash
# Build manis.app on macOS and package it as a .dmg (or .zip if hdiutil/create-dmg
# isn't available — e.g. on GitHub-hosted runners without homebrew).
#
# Usage:
#     PYTHON_BIN=/path/to/framework-python3.13 ./scripts/build-mac.sh
#
# Outputs:
#     dist/manis-{version}-{arch}.dmg     (if create-dmg is installed)
#     dist/manis-{version}-{arch}.zip    (fallback)
#
# Environment:
#     PYTHON_BIN  framework build of Python 3.13 (default: brew cellar path)
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13}"
BUILD_LABEL="macOS"
ARCH="$(uname -m)"   # x86_64 or arm64

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=build-common.sh
source "$SCRIPT_DIR/build-common.sh"

# Framework check (skip on CI: runners always satisfy this)
if [[ "${SKIP_FRAMEWORK_CHECK:-0}" != "1" ]]; then
    if ! "$PYTHON_BIN" -c "import sys, sysconfig; sys.exit(0 if sysconfig.get_config_var('PYTHONFRAMEWORK') == 'Python' else 1)"; then
        echo "❌  $PYTHON_BIN is not a framework build." >&2
        echo "   Set SKIP_FRAMEWORK_CHECK=1 if you're sure (CI does this)." >&2
        exit 1
    fi
fi

APP_PATH="dist/manis.app"
if [[ ! -d "$APP_PATH" ]]; then
    echo "❌  Build failed — $APP_PATH not produced." >&2
    exit 1
fi

# Package --------------------------------------------------------------------
VERSION="${VERSION:-$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_PATH/Contents/Info.plist" 2>/dev/null || echo "0.1.0")}"
ARTIFACT_BASE="manis-${VERSION}-macOS-${ARCH}"

cd dist

if command -v create-dmg >/dev/null 2>&1; then
    echo "▶ Packaging with create-dmg → ${ARTIFACT_BASE}.dmg"
    rm -f "${ARTIFACT_BASE}.dmg"
    create-dmg \
        --volname "manis ${VERSION}" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "manis.app" 175 120 \
        --hide-extension "manis.app" \
        --app-drop-link 425 120 \
        "${ARTIFACT_BASE}.dmg" \
        "manis.app"
else
    echo "▶ create-dmg not installed — falling back to .zip"
    rm -f "${ARTIFACT_BASE}.zip"
    ditto -c -k --sequesterRsrc --keepParent "manis.app" "${ARTIFACT_BASE}.zip"
fi

cd ..
echo "✅  macOS artifact(s):"
ls -lh "dist/${ARTIFACT_BASE}".* 2>/dev/null || true