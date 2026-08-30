"""Validate a WinHelp fixture with the pinned winhlp parser."""

from __future__ import annotations

import argparse
from pathlib import Path

from winhlp.lib.hlp import HelpFile

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="sample-hlp")
    args = parser.parse_args()
    if args.id != "sample-hlp":
        raise SystemExit(f"unsupported fixture id: {args.id}")
    path = ROOT / "tests" / "fixtures" / "sample.hlp"
    help_file = HelpFile(filepath=str(path))
    assert help_file.header is not None
    assert help_file.directory is not None
    assert help_file.system is not None
    assert help_file.topic is not None
    assert not help_file.parse_errors
    print("sample-hlp: winhlp HelpFile parse and internal files passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
