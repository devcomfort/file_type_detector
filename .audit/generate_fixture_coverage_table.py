"""Generate a complete, separate table for the current fixture corpus."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".audit" / "fixture-coverage-table.csv"

FIELDS = [
    "id",
    "probe",
    "fixture",
    "mime_types",
    "ground_truth_extensions",
    "ground_truth_filenames",
    "review_status",
    "format_validity",
    "validator",
    "identifiability",
    "reproduction_method",
    "declared_reproduction_tier",
    "disk_sha_consistency",
    "reproduction_verified",
    "pinned_source_sha_verified",
    "source_manifest_status",
    "sha256",
    "sha256_on_disk",
    "evidence_status",
]


def build_rows() -> list[dict[str, str]]:
    candidates = json.loads(
        (ROOT / "tests/truth/backend_inventory_candidates.json").read_text()
    )["records"]
    manifest = json.loads((ROOT / "tests/truth/source_manifest.json").read_text())[
        "fixtures"
    ]
    rows: list[dict[str, str]] = []
    for record in candidates:
        source = record.get("source_integrity") or {}
        validity = record.get("format_validity") or {}
        review = record.get("ground_truth_review") or {}
        fixture = ROOT / record["fixture"]
        disk_sha = (
            hashlib.sha256(fixture.read_bytes()).hexdigest()
            if fixture.is_file()
            else "missing"
        )
        source_kind = source.get("kind", "unknown")
        if source_kind == "generated":
            method = source.get("generator_symbol", "registered generator")
            tier = source.get("tier", "unclassified")
            reproduction = f"generated:{method}; tier={tier}"
        elif source_kind == "external":
            reproduction = f"external:{source.get('origin_url', 'unrecorded source')}"
        else:
            reproduction = record.get("provenance", "unrecorded")
        if disk_sha == "missing":
            disk_consistency = "missing fixture"
        elif disk_sha != record.get("sha256"):
            disk_consistency = "SHA256 mismatch"
        else:
            disk_consistency = "SHA256 match"
        declared_tier = source.get("tier", "unclassified")
        reproduction_verified = str(source.get("reproduction_verified", "not-executed"))
        pinned_source_verified = str(source.get("blob_sha1_verified", "not-applicable"))
        probe = record.get("probe_filename") or record.get("probe_extension", "")
        rows.append(
            {
                "id": record["id"],
                "probe": probe,
                "fixture": record["fixture"],
                "mime_types": "; ".join(record["ground_truth"].get("mime_types", [])),
                "ground_truth_extensions": "; ".join(
                    record["ground_truth"].get("extensions", [])
                ),
                "ground_truth_filenames": "; ".join(
                    record["ground_truth"].get("filenames", [])
                ),
                "review_status": review.get("status", "missing"),
                "format_validity": validity.get("status", "missing"),
                "validator": validity.get("validator", ""),
                "identifiability": str(record.get("content_identifiability") or ""),
                "reproduction_method": reproduction,
                "declared_reproduction_tier": declared_tier,
                "disk_sha_consistency": disk_consistency,
                "reproduction_verified": reproduction_verified,
                "pinned_source_sha_verified": pinned_source_verified,
                "source_manifest_status": manifest.get(record["id"], {}).get(
                    "status", "missing"
                ),
                "sha256": record.get("sha256", ""),
                "sha256_on_disk": disk_sha,
                "evidence_status": (
                    "complete" if record.get("ground_truth_evidence") else "missing"
                ),
            }
        )
    return rows


def render(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = render(build_rows())
    if args.check:
        current = args.output.read_text(encoding="utf-8")
        if current != generated:
            raise SystemExit("fixture coverage table is stale")
        print("fixture coverage table: current")
        return 0
    args.output.write_text(generated, encoding="utf-8")
    print(f"wrote {len(generated.splitlines()) - 1} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
