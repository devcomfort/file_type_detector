"""Non-destructive full corpus audit.

Writes a new audit artifact; never rewrites inventory or the coverage table.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".audit" / "full-corpus-audit-latest.json"
CFB_CONFLICT_IDS = {
    "sample-msi",
    "sample-one",
    "sample-vsd",
    "sample-dot",
    "sample-msg",
    "sample-rfa",
    "sample-rte",
    "sample-rvt",
    "sample-wps",
    "sample-xlt",
    "sample-vdw",
    "sample-vsdm",
    "sample-vsdx",
}


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
    matrix = json.loads((ROOT / ".audit/w3-w4-audit-matrix.json").read_text())
    by_id = {r["id"]: r for r in candidates}
    rows = []
    by_sha: dict[str, list[str]] = defaultdict(list)
    for record in candidates:
        path = ROOT / record["fixture"]
        exists = path.is_file()
        disk_sha = hashlib.sha256(path.read_bytes()).hexdigest() if exists else None
        if disk_sha:
            by_sha[disk_sha].append(record["id"])
        source = record.get("source_integrity") or {}
        validity = record.get("format_validity") or {}
        rows.append(
            {
                "id": record["id"],
                "fixture": record["fixture"],
                "review_status": record.get("ground_truth_review", {}).get("status"),
                "exists": exists,
                "inventory_sha256": record.get("sha256"),
                "disk_sha256": disk_sha,
                "sha_match": exists and disk_sha == record.get("sha256"),
                "manifest_sha_match": manifest.get(record["id"], {}).get("sha256")
                == record.get("sha256"),
                "source_kind": source.get("kind"),
                "declared_reproduction_tier": source.get("tier"),
                "generator_symbol": source.get("generator_symbol"),
                "format_validity": validity.get("status"),
                "validator": validity.get("validator"),
                "evidence_present": bool(record.get("ground_truth_evidence")),
                "identifiability": record.get("content_identifiability"),
                "cfb_conflict": record["id"] in CFB_CONFLICT_IDS,
                "duplicate_sha_group": [],
            }
        )
    for row in rows:
        row["duplicate_sha_group"] = by_sha.get(row["disk_sha256"] or "", [])
    duplicate_conflicts = []
    for sha, ids in by_sha.items():
        if len(ids) > 1:
            gt = [by_id[i]["ground_truth"] for i in ids]
            if len({json.dumps(x, sort_keys=True) for x in gt}) > 1:
                duplicate_conflicts.append({"sha256": sha, "ids": ids})
    matrix_candidate_inconsistencies = []
    for row in matrix["actions"]:
        inventory_id = row.get("inventory_id")
        if not inventory_id:
            continue
        candidate = by_id.get(inventory_id)
        if candidate is None:
            matrix_candidate_inconsistencies.append(
                {
                    "action": row["action"],
                    "inventory_id": inventory_id,
                    "reason": "matrix id absent from candidates",
                }
            )
            continue
        candidate_validity = candidate.get("format_validity") or {}
        candidate_status = candidate_validity.get("status")
        matrix_status = row.get("format_validity")
        if matrix_status != candidate_status:
            matrix_candidate_inconsistencies.append(
                {
                    "action": row["action"],
                    "inventory_id": inventory_id,
                    "reason": f"format_validity matrix={matrix_status}, candidate={candidate_status}",
                }
            )
        if row.get("content_identifiability") != candidate.get(
            "content_identifiability"
        ):
            matrix_candidate_inconsistencies.append(
                {
                    "action": row["action"],
                    "inventory_id": inventory_id,
                    "reason": "content_identifiability differs",
                }
            )
        matrix_evidence = set(row.get("validator_evidence") or [])
        candidate_evidence = set(candidate_validity.get("evidence") or [])
        if not matrix_evidence <= candidate_evidence:
            matrix_candidate_inconsistencies.append(
                {
                    "action": row["action"],
                    "inventory_id": inventory_id,
                    "reason": "matrix validator evidence missing from candidate",
                }
            )
        promoted = candidate.get("ground_truth_review", {}).get("status") == "verified"
        if bool(row.get("promotion_input")) != promoted:
            matrix_candidate_inconsistencies.append(
                {
                    "action": row["action"],
                    "inventory_id": inventory_id,
                    "reason": "promotion_input differs from review_status",
                }
            )
    report = {
        "schema_version": 2,
        "generated_by": ".audit/full-corpus-audit.py",
        "candidate_count": len(candidates),
        "authoritative_count": len(authoritative),
        "rows": rows,
        "duplicate_sha_conflicts": duplicate_conflicts,
        "cfb_conflict_ids": sorted(CFB_CONFLICT_IDS),
        "matrix_candidate_inconsistencies": matrix_candidate_inconsistencies,
        "queues": {
            "missing_fixture": [r["id"] for r in rows if not r["exists"]],
            "sha_mismatch": [r["id"] for r in rows if not r["sha_match"]],
            "manifest_mismatch": [r["id"] for r in rows if not r["manifest_sha_match"]],
            "missing_evidence": [r["id"] for r in rows if not r["evidence_present"]],
            "missing_identifiability": [
                r["id"] for r in rows if not r["identifiability"]
            ],
            "cfb_conflicts": sorted(CFB_CONFLICT_IDS),
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"audited {len(rows)} candidates -> {args.output}")
    print(
        f"sha mismatches: {len(report['queues']['sha_mismatch'])}; duplicate GT conflicts: {len(duplicate_conflicts)}; matrix inconsistencies: {len(matrix_candidate_inconsistencies)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
