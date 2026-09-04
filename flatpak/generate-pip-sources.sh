#!/usr/bin/env bash
# Regenerate the pinned, offline Python source module used by flatpak-builder.
set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname -- "$SCRIPT_DIR")"
readonly RUNTIME_VERSION="${RUNTIME_VERSION:-25.08}"
readonly GENERATOR_VERSION="2026.5.28"
readonly TOOL_DIR="$PROJECT_DIR/.flatpak-tools/pip-generator"
readonly REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
readonly OUTPUT_NAME="python3-dependencies"

if ! command -v flatpak >/dev/null 2>&1; then
    echo "error: flatpak is required" >&2
    exit 1
fi

if ! flatpak info "org.freedesktop.Sdk//$RUNTIME_VERSION" >/dev/null 2>&1; then
    echo "error: org.freedesktop.Sdk//$RUNTIME_VERSION is not installed" >&2
    echo "install it with: flatpak install flathub org.freedesktop.Sdk//$RUNTIME_VERSION" >&2
    exit 1
fi

if ! "$TOOL_DIR/bin/python" -c "import flatpak_pip_generator" >/dev/null 2>&1; then
    echo "Installing flatpak-pip-generator $GENERATOR_VERSION in a local tool environment..."
    python3 -m venv "$TOOL_DIR"
    "$TOOL_DIR/bin/python" -m pip install --disable-pip-version-check \
        "flatpak-pip-generator==$GENERATOR_VERSION"
fi

cd "$SCRIPT_DIR/modules"
"$TOOL_DIR/bin/python" -m flatpak_pip_generator \
    --runtime="org.freedesktop.Sdk//$RUNTIME_VERSION" \
    --requirements-file="$REQUIREMENTS_FILE" \
    --output="$OUTPUT_NAME" \
    --prefer-wheels="brotli,pillow,pycryptodomex,websockets" \
    --wheel-arches="x86_64,aarch64"

echo "Generated: $SCRIPT_DIR/modules/$OUTPUT_NAME.json"
