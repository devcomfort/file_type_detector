#!/usr/bin/env bash
set -euo pipefail

# Idempotent Linux setup for audit-only fixture validators.
command -v apt-get >/dev/null || {
  echo "Unsupported Linux host: apt-get is required" >&2
  exit 2
}

sudo apt-get update
sudo apt-get install -y ffmpeg libreoffice squashfs-tools
python3 -m pip install -r .audit/requirements-apk.txt
python3 -m pip install -r .audit/requirements-hlp.txt
python3 -m pip install ds-store==1.3.3

echo "Fixture audit tools installed: ffmpeg, libreoffice, squashfs-tools, androguard, winhlp, ds-store"
