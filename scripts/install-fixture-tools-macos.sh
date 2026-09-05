#!/usr/bin/env bash
set -euo pipefail

# Idempotent macOS setup for audit-only fixture validators.
command -v brew >/dev/null || {
  echo "Unsupported macOS host: Homebrew is required; install it from https://brew.sh/" >&2
  exit 2
}

brew update
brew install ffmpeg squashfs-tools
brew install --cask libreoffice
python3 -m pip install -r .audit/requirements-apk.txt
python3 -m pip install -r .audit/requirements-hlp.txt
python3 -m pip install ds-store==1.3.3

if ! command -v unsquashfs >/dev/null; then
  echo "Unsupported macOS audit capability: unsquashfs was not installed by Homebrew" >&2
  exit 2
fi

echo "Fixture audit tools installed: ffmpeg, LibreOffice, squashfs-tools, androguard, winhlp, ds-store"
