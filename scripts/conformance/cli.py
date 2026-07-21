"""Command-line commands for seeding and reviewing conformance inventory data."""

from __future__ import annotations

import argparse
import hashlib
import json
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
        return _review_candidates(
            args.candidates,
            args.inventory,
            root=args.root,
            require_complete=args.require_complete,
        )
    except InventoryValidationError as error:
        parser.error(str(error))
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed and review backend Ground Truth conformance inventory data."
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
        json.dumps({"schema_version": 1, "records": records}, indent=2) + "\n",
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


if __name__ == "__main__":
    raise SystemExit(main())
