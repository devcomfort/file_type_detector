"""Command-line commands for seeding, reviewing, and promoting conformance inventory data."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
import re
from typing import Sequence

from scripts.conformance.inventory import InventoryValidationError, review_summary


_RECORD_ID_PATTERN = re.compile(r"[^A-Za-z0-9]+")
_REVIEW_REQUIRED_REASON = "Seeded from legacy canonical fixture data; independent Ground Truth review required"


def main(argv: Sequence[str] | None = None) -> int:
    """Run a conformance inventory command and return its process status."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "seed":
            _seed_candidates(args.source, args.output, root=args.root)
            return 0
        if args.command == "review":
            return _review_candidates(
                args.candidates,
                args.inventory,
                root=args.root,
                require_complete=args.require_complete,
            )
        return _promote_candidates(
            args.candidates,
            args.inventory,
            root=args.root,
            ids=args.ids,
            all_clean=args.all_clean,
            reviewer=args.reviewer,
            evidence=args.evidence,
            review_date=args.date,
            fix_extensions=args.fix_extensions,
        )
    except InventoryValidationError as error:
        parser.error(str(error))
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed, review, and promote backend Ground Truth conformance inventory data."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    seed = commands.add_parser(
        "seed", help="Seed review candidates from legacy truth data."
    )
    seed.add_argument("--source", type=Path, required=True)
    seed.add_argument("--output", type=Path, required=True)
    seed.add_argument("--root", type=Path, required=True)

    review = commands.add_parser("review", help="Report candidate review status.")
    review.add_argument("--candidates", type=Path, required=True)
    review.add_argument("--inventory", type=Path, required=True)
    review.add_argument("--root", type=Path, required=True)
    review.add_argument("--require-complete", action="store_true")

    promote = commands.add_parser(
        "promote",
        help="Promote reviewed candidates to verified and update the authoritative inventory.",
    )
    promote.add_argument("--candidates", type=Path, required=True)
    promote.add_argument("--inventory", type=Path, required=True)
    promote.add_argument("--root", type=Path, required=True)
    promote.add_argument("--reviewer", type=str, required=True)
    promote.add_argument("--date", type=str, default=date.today().isoformat())
    promote.add_argument("--evidence", type=str, nargs="*", default=[])
    promote.add_argument(
        "--fix-extensions",
        action="store_true",
        help="Replace conflicting legacy extensions with the fixture probe extension before promoting.",
    )
    target = promote.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--all-clean",
        action="store_true",
        help="Promote every candidate where probe_extension matches a declared extension.",
    )
    target.add_argument(
        "--ids",
        type=str,
        nargs="+",
        help="Promote specific candidate record ids.",
    )
    return parser


def _seed_candidates(source: Path, output: Path, *, root: Path) -> None:
    legacy_payload = _read_json_object(source, "legacy canonical fixture data")
    fixtures = legacy_payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise InventoryValidationError(
            "legacy canonical fixture data fixtures must be a list"
        )

    records = [_candidate_from_legacy(entry, root=root) for entry in fixtures]
    _disambiguate_record_ids(records)
    record_ids = [record["id"] for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise InventoryValidationError(
            "legacy canonical fixture data creates duplicate record ids"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"schema_version": 2, "records": records}, indent=2) + "\n",
        encoding="utf-8",
    )


def _candidate_from_legacy(entry: object, *, root: Path) -> dict[str, object]:
    fixture = _require_mapping(entry, "legacy fixture")
    fixture_path = _require_string(fixture.get("path"), "legacy fixture path")
    mime = _require_string(
        fixture.get("canonical_mime"), "legacy fixture canonical_mime"
    )
    extensions = _require_string_list(
        fixture.get("canonical_extensions"), "legacy fixture canonical_extensions"
    )
    provenance = _require_string(fixture.get("provenance"), "legacy fixture provenance")

    return {
        "id": _record_id(fixture_path),
        "fixture": fixture_path,
        "sha256": _file_digest(_resolve_fixture(root, fixture_path)),
        "probe_extension": _fixture_extension(fixture_path),
        "ground_truth": {
            "mime_types": [mime],
            "extensions": extensions,
        },
        "provenance": provenance,
        "ground_truth_review": {
            "status": "needs_review",
            "reason": _REVIEW_REQUIRED_REASON,
        },
        "backends": ["lexical", "magic", "magika", "hybrid"],
    }


def _disambiguate_record_ids(records: list[dict[str, object]]) -> None:
    counts: dict[str, int] = {}
    for record in records:
        record_id = record["id"]
        if not isinstance(record_id, str):
            raise InventoryValidationError("candidate record id must be a string")
        counts[record_id] = counts.get(record_id, 0) + 1

    for record in records:
        record_id = record["id"]
        fixture_path = record["fixture"]
        if not isinstance(record_id, str) or not isinstance(fixture_path, str):
            raise InventoryValidationError(
                "candidate record must contain id and fixture"
            )
        if counts[record_id] > 1:
            path_digest = hashlib.sha256(fixture_path.encode("utf-8")).hexdigest()[:12]
            record["id"] = f"{record_id}--{path_digest}"


def _read_json_object(path: Path, description: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InventoryValidationError(f"cannot read {description}: {error}") from error
    if not isinstance(payload, dict):
        raise InventoryValidationError(f"{description} must be a JSON object")
    return payload


def _resolve_fixture(root: Path, declared_path: str) -> Path:
    path = Path(declared_path)
    if path.is_absolute() or ".." in path.parts:
        raise InventoryValidationError("legacy fixture path must be root-relative")

    resolved_root = root.resolve()
    fixture = (resolved_root / path).resolve()
    if not fixture.is_relative_to(resolved_root) or not fixture.is_file():
        raise InventoryValidationError(
            "legacy fixture path must name a root-relative file"
        )
    return fixture


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fixture:
        for chunk in iter(lambda: fixture.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_id(path: str) -> str:
    record_id = _RECORD_ID_PATTERN.sub("-", Path(path).name).strip("-")
    if not record_id:
        raise InventoryValidationError("legacy fixture path cannot produce a record id")
    return record_id


def _fixture_extension(path: str) -> str:
    extension = Path(path).suffix.lower()
    if not extension:
        raise InventoryValidationError("legacy fixture path must have an extension")
    return extension


def _require_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InventoryValidationError(f"{field} must be an object")
    return value


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InventoryValidationError(f"{field} must be a non-empty string")
    return value


def _require_string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise InventoryValidationError(f"{field} must be a non-empty list")
    return [_require_string(item, field) for item in value]


def _review_candidates(
    candidates: Path,
    inventory: Path,
    *,
    root: Path,
    require_complete: bool,
) -> int:
    summary = review_summary(candidates, inventory, root=root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if require_complete and summary["unresolved_count"]:
        return 2
    return 0


def _promote_candidates(
    candidates_path: Path,
    inventory_path: Path,
    *,
    root: Path,
    ids: list[str] | None,
    all_clean: bool,
    reviewer: str,
    evidence: list[str],
    review_date: str,
    fix_extensions: bool,
) -> int:
    """Promote selected candidates to verified and sync the authoritative inventory."""
    candidates_payload = _read_json_object(candidates_path, "candidate inventory")
    inventory_payload = _read_json_object(inventory_path, "authoritative inventory")

    raw_records = candidates_payload.get("records")
    if not isinstance(raw_records, list):
        raise InventoryValidationError("candidate inventory records must be a list")
    records: list[dict[str, object]] = list(raw_records)

    # A conflicting legacy declaration is not an alias. The fixture suffix is the
    # reviewed fact used to repair the candidate before promotion.
    fixed: list[str] = []
    if fix_extensions:
        for record in records:
            record_id = _require_string(record.get("id"), "record id")
            review = _require_mapping(
                record.get("ground_truth_review", {}), f"{record_id} review"
            )
            if review.get("status") != "needs_review":
                continue
            probe = _require_string(
                record.get("probe_extension"), f"{record_id} probe_extension"
            )
            gt = _require_mapping(
                record.get("ground_truth", {}), f"{record_id} ground_truth"
            )
            declared = _require_string_list(
                gt.get("extensions"), f"{record_id} extensions"
            )
            if probe not in declared:
                gt["extensions"] = [probe]
                review["reason"] = (
                    f"Extension corrected: contradictory legacy declarations "
                    f"{declared} replaced with fixture probe extension {probe}; "
                    "independent Ground Truth review required"
                )
                fixed.append(record_id)

    # Build promotion set, excluding records fixed in this call (two-phase contract:
    # --fix-extensions corrects aliases but does NOT promote; a separate call
    # with fresh evidence promotes).
    promote_ids: set[str]
    if ids is not None:
        promote_ids = set(ids)
    else:
        promote_ids = {
            _require_string(r.get("id"), "record id")
            for r in records
            if isinstance(r, dict)
            and r.get("probe_extension")
            in _require_string_list(
                _require_mapping(r.get("ground_truth", {}), "ground_truth").get(
                    "extensions"
                ),
                "extensions",
            )
        }

    # Two-phase contract: --fix-extensions corrects aliases but does NOT
    # promote in the same call. Fixed records stay needs_review until a
    # separate promote call with fresh evidence runs.
    promote_ids.difference_update(fixed)

    promoted: list[str] = []
    skipped: list[str] = []
    verified_records: list[dict[str, object]] = []

    for record in records:
        record_id = _require_string(record.get("id"), "record id")
        if record_id not in promote_ids:
            review = _require_mapping(
                record.get("ground_truth_review", {}), f"{record_id} review"
            )
            if review.get("status") == "verified":
                verified_records.append(record)
            continue

        current_review = _require_mapping(
            record.get("ground_truth_review", {}), f"{record_id} review"
        )
        current_status = current_review.get("status")
        if current_status == "verified":
            skipped.append(record_id)
            verified_records.append(record)
            continue

        provenance = _require_string(
            record.get("provenance"), f"{record_id} provenance"
        )
        combined_evidence = [provenance] + list(evidence)

        # Normalize MIME types and extensions to lowercase (contract requires canonical form for verified records)
        gt = _require_mapping(
            record.get("ground_truth", {}), f"{record_id} ground_truth"
        )
        gt["mime_types"] = [
            m.lower()
            for m in _require_string_list(
                gt.get("mime_types"), f"{record_id} mime_types"
            )
        ]
        gt["extensions"] = [
            ext.lower()
            for ext in _require_string_list(
                gt.get("extensions"), f"{record_id} extensions"
            )
        ]

        record["ground_truth_review"] = {
            "status": "verified",
            "reviewed_by": reviewer,
            "reviewed_at": review_date,
            "evidence": combined_evidence,
        }
        promoted.append(record_id)
        verified_records.append(record)

    # Pre-write validation: every promoted record must carry all three truth axes
    for rec in verified_records:
        rid = rec.get("id", "?")
        si = rec.get("source_integrity")
        if not si:
            raise InventoryValidationError(
                f"cannot promote {rid!r}: source_integrity axis missing; "
                "add provenance data or exclude this record"
            )
        fv = rec.get("format_validity")
        if not fv or fv.get("status") != "verified":
            raise InventoryValidationError(
                f"cannot promote {rid!r}: format_validity must be verified; "
                "run an independent parser validator first"
            )
        if not rec.get("ground_truth_evidence"):
            raise InventoryValidationError(
                f"cannot promote {rid!r}: ground_truth_evidence missing; "
                "every claimed MIME/extension needs authority + reference"
            )
    # Write updated candidates
    candidates_payload["records"] = records
    candidates_path.write_text(
        json.dumps(candidates_payload, indent=2) + "\n", encoding="utf-8"
    )

    # Write updated inventory
    inventory_payload["records"] = verified_records
    inventory_path.write_text(
        json.dumps(inventory_payload, indent=2) + "\n", encoding="utf-8"
    )

    # Validate
    summary = review_summary(candidates_path, inventory_path, root=root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"\nPromoted: {len(promoted)}")
    if fixed:
        print(f"Extensions fixed: {len(fixed)}")
    if skipped:
        print(f"Already verified (skipped): {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
