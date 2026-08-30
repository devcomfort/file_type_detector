"""Generate and verify the separate fixture coverage report.

This report consumes the checked-in audit matrix. Platform-specific validators
(such as unsquashfs) run in their dedicated CI jobs, not during report generation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".audit" / "file-coverage-latest.json"


def build_report() -> dict[str, object]:
    candidates = json.loads(
        (ROOT / "tests/truth/backend_inventory_candidates.json").read_text()
    )["records"]
    authoritative = json.loads(
        (ROOT / "tests/truth/backend_inventory.json").read_text()
    )["records"]
    matrix = json.loads((ROOT / ".audit/w3-w4-audit-matrix.json").read_text())
    statuses: Counter[str] = Counter()
    for row in matrix["actions"]:
        if not row.get("inventory_id"):
            statuses["missing_inventory"] += 1
        else:
            statuses[row.get("format_validity", "not-run")] += 1
    return {
        "schema_version": 1,
        "generated_by": ".audit/coverage-report.py",
        "candidate": {
            "total": len(candidates),
            "verified": sum(
                r["ground_truth_review"]["status"] == "verified" for r in candidates
            ),
            "excluded": sum(
                r["ground_truth_review"]["status"] == "excluded" for r in candidates
            ),
        },
        "authoritative": {"total": len(authoritative)},
        "w3_matrix": {
            "total": len(matrix["actions"]),
            **dict(statuses),
            "missing_actions": [
                r["action"] for r in matrix["actions"] if not r.get("inventory_id")
            ],
            "needs_review_actions": [
                r["action"]
                for r in matrix["actions"]
                if r.get("inventory_id") and r.get("format_validity") == "needs_review"
            ],
        },
        "notes": [
            "Recognition-label coverage and suffix coverage are separate metrics.",
            "Promotion requires all truth axes and evidence.",
            "Platform-specific validators run in dedicated CI jobs before matrix updates.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.check:
        actual = json.loads(OUTPUT.read_text())
        if actual != report:
            print("file coverage report is stale", file=sys.stderr)
            return 1
        print("file coverage report: current")
        return 0
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
