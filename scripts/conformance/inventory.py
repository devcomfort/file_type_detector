"""Load and validate independently reviewed conformance inventory data."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from scripts.conformance.types import (
    FixtureReference,
    GroundTruth,
    GroundTruthReview,
    InventoryRecord,
)


class InventoryValidationError(ValueError):
    """Raised when inventory data cannot safely drive conformance collection."""


_SUPPORTED_REVIEW_STATUSES = frozenset({"verified", "needs_review", "excluded"})
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def load_verified_inventory(
    candidates_path: Path,
    inventory_path: Path,
    *,
    root: Path,
) -> tuple[InventoryRecord, ...]:
    """Return authoritative records after validating their reviewed candidates."""

    candidates = _load_document(candidates_path, root=root, role="candidate")
    authoritative = _load_document(inventory_path, root=root, role="authoritative")
    _validate_pairs(candidates, authoritative)
    return authoritative


def review_summary(
    candidates_path: Path,
    inventory_path: Path,
    *,
    root: Path,
) -> dict[str, object]:
    """Summarize candidate review state without admitting unreviewed records."""

    candidates = _load_document(candidates_path, root=root, role="candidate")
    authoritative = _load_document(inventory_path, root=root, role="authoritative")
    _validate_pairs(candidates, authoritative)

    unresolved = [
        {
            "id": record.id,
            "reason": record.ground_truth_review.reason,
            "mimes": list(record.ground_truth.mimes),
            "extensions": list(record.ground_truth.extensions),
        }
        for record in candidates
        if record.ground_truth_review.status == "needs_review"
    ]
    verified_count = sum(
        record.ground_truth_review.status == "verified" for record in candidates
    )
    return {
        "candidate_count": len(candidates),
        "verified_count": verified_count,
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
    }


def _load_document(path: Path, *, root: Path, role: str) -> tuple[InventoryRecord, ...]:
    payload = _load_json(path)
    if payload.get("schema_version") != 1:
        raise InventoryValidationError(f"{role} inventory must use schema_version 1")

    records_payload = payload.get("records")
    if not isinstance(records_payload, list):
        raise InventoryValidationError(f"{role} inventory records must be a list")

    records = tuple(
        _parse_record(raw_record, root=root, role=role)
        for raw_record in records_payload
    )
    _validate_unique_ids(records, role=role)
    return records


def _load_json(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InventoryValidationError(
            f"cannot read inventory {path}: {error}"
        ) from error

    if not isinstance(payload, dict):
        raise InventoryValidationError(f"inventory {path} must be a JSON object")
    return payload


def _parse_record(
    raw_record: object,
    *,
    root: Path,
    role: str,
) -> InventoryRecord:
    record = _require_mapping(raw_record, f"{role} record")
    record_id = _require_string(record.get("id"), f"{role} record id")

    fixture = _parse_fixture(
        _require_string(record.get("fixture"), f"{record_id} fixture"),
        _require_string(record.get("sha256"), f"{record_id} sha256"),
        root=root,
        record_id=record_id,
    )
    probe_extension = _parse_extension(
        record.get("probe_extension"), f"{record_id} probe_extension"
    )
    provenance = _require_string(record.get("provenance"), f"{record_id} provenance")
    review = _parse_review(
        _require_mapping(
            record.get("ground_truth_review"), f"{record_id} ground_truth_review"
        ),
        record_id=record_id,
    )
    if role == "authoritative" and review.status != "verified":
        raise InventoryValidationError(
            f"authoritative record {record_id!r} requires verified review"
        )
    ground_truth = _parse_ground_truth(
        _require_mapping(record.get("ground_truth"), f"{record_id} ground_truth"),
        record_id=record_id,
        require_canonical=role == "authoritative" or review.status == "verified",
    )
    backends = _parse_backends(record.get("backends"), f"{record_id} backends")
    return InventoryRecord(
        id=record_id,
        fixture=fixture,
        probe_extension=probe_extension,
        ground_truth=ground_truth,
        provenance=provenance,
        ground_truth_review=review,
        backends=backends,
    )


def _parse_fixture(
    path: str,
    digest: str,
    *,
    root: Path,
    record_id: str,
) -> FixtureReference:
    if not _SHA256_PATTERN.fullmatch(digest):
        raise InventoryValidationError(f"{record_id} sha256 must be lowercase SHA-256")

    fixture_path = _resolve_fixture(root, path, record_id=record_id)
    if _file_digest(fixture_path) != digest:
        raise InventoryValidationError(f"{record_id} fixture digest mismatch")
    return FixtureReference(path=path, sha256=digest)


def _resolve_fixture(root: Path, path: str, *, record_id: str) -> Path:
    declared_path = Path(path)
    if declared_path.is_absolute() or ".." in declared_path.parts:
        raise InventoryValidationError(
            f"{record_id} fixture.path must be root-relative"
        )

    resolved_root = root.resolve()
    resolved_fixture = (resolved_root / declared_path).resolve()
    if not resolved_fixture.is_relative_to(resolved_root):
        raise InventoryValidationError(
            f"{record_id} fixture.path must be root-relative"
        )
    if not resolved_fixture.is_file():
        raise InventoryValidationError(f"{record_id} fixture.path does not name a file")
    return resolved_fixture


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fixture:
        for chunk in iter(lambda: fixture.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_ground_truth(
    ground_truth: Mapping[str, object],
    *,
    record_id: str,
    require_canonical: bool,
) -> GroundTruth:
    return GroundTruth(
        mimes=_parse_mimes(
            ground_truth.get("mime_types"),
            f"{record_id} ground_truth.mime_types",
            require_canonical=require_canonical,
        ),
        extensions=_parse_extensions(
            ground_truth.get("extensions"),
            f"{record_id} ground_truth.extensions",
            require_canonical=require_canonical,
        ),
    )


def _parse_mimes(
    value: object,
    field: str,
    *,
    require_canonical: bool,
) -> tuple[str, ...]:
    values = _require_string_list(value, field)
    if require_canonical and any(mime != mime.lower() for mime in values):
        raise InventoryValidationError(f"{field} must be lowercase")
    return values


def _parse_extensions(
    value: object,
    field: str,
    *,
    require_canonical: bool,
) -> tuple[str, ...]:
    values = _require_string_list(value, field)
    for extension in values:
        if not extension.startswith("."):
            raise InventoryValidationError(f"{field} must use dotted extensions")
        if require_canonical and extension != extension.lower():
            raise InventoryValidationError(f"{field} must be lowercase")
    return values


def _parse_extension(value: object, field: str) -> str:
    extension = _require_string(value, field)
    if not extension.startswith("."):
        raise InventoryValidationError(f"{field} must use a dotted extension")
    if extension != extension.lower():
        raise InventoryValidationError(f"{field} must be lowercase")
    return extension


def _parse_backends(value: object, field: str) -> tuple[str, ...]:
    backends = _require_string_list(value, field)
    expected = ("lexical", "magic", "magika", "hybrid")
    if backends != expected:
        raise InventoryValidationError(
            f"{field} must list lexical, magic, magika, hybrid"
        )
    return backends


def _parse_review(
    review: Mapping[str, object],
    *,
    record_id: str,
) -> GroundTruthReview:
    status = _require_string(review.get("status"), f"{record_id} review status")
    if status not in _SUPPORTED_REVIEW_STATUSES:
        raise InventoryValidationError(f"{record_id} review status is unsupported")

    if status == "verified":
        reviewed_by = review.get("reviewed_by")
        reviewed_at = review.get("reviewed_at")
        evidence_payload = review.get("evidence")
        if (
            not isinstance(reviewed_by, str)
            or not reviewed_by.strip()
            or not isinstance(reviewed_at, str)
            or not _is_iso_date(reviewed_at)
            or not isinstance(evidence_payload, list)
            or not evidence_payload
        ):
            raise InventoryValidationError(
                f"{record_id} verified review requires reviewer, date, and evidence"
            )
        evidence = tuple(
            _require_string(item, f"{record_id} evidence") for item in evidence_payload
        )
        return GroundTruthReview(
            status=status,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            evidence=evidence,
            reason=None,
        )

    reason = _require_string(review.get("reason"), f"{record_id} review reason")
    return GroundTruthReview(
        status=status,
        reviewed_by=None,
        reviewed_at=None,
        evidence=(),
        reason=reason,
    )


def _is_iso_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _require_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise InventoryValidationError(f"{field} must be an object")
    return value


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InventoryValidationError(f"{field} must be a non-empty string")
    return value


def _require_string_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise InventoryValidationError(f"{field} must be a non-empty list")
    values = tuple(_require_string(item, field) for item in value)
    return values


def _validate_unique_ids(records: tuple[InventoryRecord, ...], *, role: str) -> None:
    record_ids = [record.id for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise InventoryValidationError(
            f"{role} inventory contains duplicate record ids"
        )


def _validate_pairs(
    candidates: tuple[InventoryRecord, ...],
    authoritative: tuple[InventoryRecord, ...],
) -> None:
    candidates_by_id = {record.id: record for record in candidates}
    authoritative_by_id = {record.id: record for record in authoritative}

    for record in authoritative:
        candidate = candidates_by_id.get(record.id)
        if candidate is None:
            raise InventoryValidationError(
                f"authoritative record {record.id!r} has no matching candidate"
            )
        if candidate.ground_truth_review.status != "verified":
            raise InventoryValidationError(
                f"authoritative record {record.id!r} requires a verified candidate"
            )
        if record != candidate:
            raise InventoryValidationError(
                f"authoritative record {record.id!r} must be fact-identical to its candidate"
            )

    for candidate in candidates:
        if candidate.ground_truth_review.status != "verified":
            continue
        authoritative_record = authoritative_by_id.get(candidate.id)
        if authoritative_record is None:
            raise InventoryValidationError(
                f"verified candidate {candidate.id!r} requires an authoritative record"
            )
        if authoritative_record != candidate:
            raise InventoryValidationError(
                f"verified candidate {candidate.id!r} requires a fact-identical authoritative record"
            )
