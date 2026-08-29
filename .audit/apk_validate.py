"""Independent APK container validation using pinned androguard.

The fixture is intentionally not promoted as a semantic Android application:
the validator proves ZIP/binary-AXML parsing only. Install the exact pinned
dependency from ``.audit/requirements-apk.txt`` before running this script.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from androguard.core.apk import APK

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="sample-apk")
    args = parser.parse_args()
    if args.id != "sample-apk":
        raise SystemExit(f"unsupported fixture id: {args.id}")
    path = ROOT / "tests" / "fixtures" / "sample.apk"
    apk = APK(str(path))
    if not apk.is_valid_APK():
        raise SystemExit("androguard rejected APK container/binary AXML")
    print("sample-apk: androguard APK.is_valid_APK container parse passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
