#!/bin/bash
# Generate Python dependencies for Flatpak build
#
# This script uses flatpak-pip-generator to create a list of all
# required Python packages and their transitive dependencies so they
# can be downloaded and added to the manifest as sources.
#
# The manifest builds Python dependencies directly from PyPI using pip,
# so this script is only needed if you want fully offline / pinned builds.
#
# Prerequisites:
#   pip install flatpak-pip-generator
#
# Usage:
#   ./flatpak/generate-pip-sources.sh
#
# This will write a temporary requirements lock for reference.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Locking Python dependencies for Flatpak..."

# Freeze current installed versions for reproducible builds
python3 -m pip freeze > "$SCRIPT_DIR/requirements-flatpak.lock"

echo "Lock file written: $SCRIPT_DIR/requirements-flatpak.lock"
echo ""
echo "Next steps:"
echo "  1. Review platform dependencies in the manifest"
echo "  2. Build with: flatpak-builder --repo=repo --force-clean build-dir $SCRIPT_DIR/io.github.hmidani_abdelilah.Media_Downloader.json"
echo "  3. Bundle with: flatpak build-bundle repo io.github.hmidani_abdelilah.Media_Downloader.flatpak io.github.hmidani_abdelilah.Media_Downloader"
