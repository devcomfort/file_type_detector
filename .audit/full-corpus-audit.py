"""Non-destructive full corpus audit.

Writes a new audit artifact; never rewrites inventory or the coverage table.
Checks fixture existence, SHA256, manifest consistency, duplicate-byte groups,
and records validator/reproduction work queues for follow-up execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".audit" / "full-corpus-audit-latest.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    candidates = json.loads(
        (ROOT / "tests/truth/backend_inventory_candidates.json").read_text()
    )["records"]
    authoritative = json.loads(
        (ROOT / "tests/truth/backend_inventory.json").read_text()
    )["records"]
    manifest = json.loads((ROOT / "tests/truth/source_manifest.json").read_text())[
        "fixtures"
    ]
    rows = []
    by_sha: dict[str, list[str]] = defaultdict(list)
    for record in candidates:
        path = ROOT / record["fixture"]
        exists = path.is_file()
        disk_sha = hashlib.sha256(path.read_bytes()).hexdigest() if exists else None
        if disk_sha:
            by_sha[disk_sha].append(record["id"])
        manifest_entry = manifest.get(record["id"], {})
        source = record.get("source_integrity") or {}
        rows.append(
            {
                "id": record["id"],
                "fixture": record["fixture"],
                "review_status": record.get("ground_truth_review", {}).get("status"),
                "exists": exists,
                "inventory_sha256": record.get("sha256"),
                "disk_sha256": disk_sha,
                "sha_match": exists and disk_sha == record.get("sha256"),
                "manifest_sha_match": manifest_entry.get("sha256")
                == record.get("sha256"),
                "manifest_status": manifest_entry.get("status"),
                "source_kind": source.get("kind"),
                "declared_reproduction_tier": source.get("tier"),
                "generator_symbol": source.get("generator_symbol"),
                "format_validity": (record.get("format_validity") or {}).get("status"),
                "validator": (record.get("format_validity") or {}).get("validator"),
                "evidence_present": bool(record.get("ground_truth_evidence")),
                "identifiability": record.get("content_identifiability"),
                "generator_reproduction": "not-run by portable audit; run registered-generator gate separately",
                "duplicate_sha_group": [],
            }
        )
    for row in rows:
        row["duplicate_sha_group"] = by_sha.get(row["disk_sha256"] or "", [])
    duplicate_conflicts = []
    for sha, ids in by_sha.items():
        if len(ids) > 1:
            gt = [
                next(r for r in candidates if r["id"] == i)["ground_truth"] for i in ids
            ]
            if len({json.dumps(x, sort_keys=True) for x in gt}) > 1:
                duplicate_conflicts.append({"sha256": sha, "ids": ids})
    report = {
        "schema_version": 1,
        "generated_by": ".audit/full-corpus-audit.py",
        "candidate_count": len(candidates),
        "authoritative_count": len(authoritative),
        "rows": rows,
        "duplicate_sha_conflicts": duplicate_conflicts,
        "queues": {
            "missing_fixture": [r["id"] for r in rows if not r["exists"]],
            "sha_mismatch": [r["id"] for r in rows if not r["sha_match"]],
            "manifest_mismatch": [r["id"] for r in rows if not r["manifest_sha_match"]],
            "missing_evidence": [r["id"] for r in rows if not r["evidence_present"]],
            "missing_identifiability": [
                r["id"] for r in rows if not r["identifiability"]
            ],
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"audited {len(rows)} candidates -> {args.output}")
    print(
        f"sha mismatches: {len(report['queues']['sha_mismatch'])}; duplicate GT conflicts: {len(duplicate_conflicts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
