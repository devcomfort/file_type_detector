"""Independent APK validation using androguard.

Install androguard in the audit environment before running this script.
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
        raise SystemExit("androguard rejected APK")
    print("sample-apk: androguard APK.is_valid_APK passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
