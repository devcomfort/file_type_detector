"""Load and validate independently reviewed conformance inventory data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from scripts.conformance.types import (
    FixtureReference,
    FormatValidity,
    GroundTruth,
    GroundTruthEvidence,
    GroundTruthReview,
    InventoryRecord,
    SourceIntegrity,
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
            "provenance": record.provenance,
            "mimes": list(record.ground_truth.mimes),
            "extensions": list(record.ground_truth.extensions),
        }
        for record in candidates
        if record.ground_truth_review.status == "needs_review"
    ]
    verified = [
        record
        for record in candidates
        if record.ground_truth_review.status == "verified"
    ]
    excluded = [
        record
        for record in candidates
        if record.ground_truth_review.status == "excluded"
    ]
    return {
        "candidate_count": len(candidates),
        "candidate_suffix_count": _unique_suffix_count(candidates),
        "verified_count": len(verified),
        "verified_suffix_count": _unique_suffix_count(verified),
        "unresolved_count": len(unresolved),
        "unresolved_suffix_count": _unique_suffix_count(
            [
                record
                for record in candidates
                if record.ground_truth_review.status == "needs_review"
            ]
        ),
        "excluded_count": len(excluded),
        "excluded_suffix_count": _unique_suffix_count(excluded),
        "unresolved": unresolved,
    }


def _unique_suffix_count(records: Sequence[InventoryRecord]) -> int:
    return len({record.probe_extension for record in records})


def _load_document(path: Path, *, root: Path, role: str) -> tuple[InventoryRecord, ...]:
    payload = _load_json(path)
    version = payload.get("schema_version")
    if version != 2:
        raise InventoryValidationError(f"{role} inventory must use schema_version 2")

    records_payload = payload.get("records")
    if not isinstance(records_payload, list):
        raise InventoryValidationError(f"{role} inventory records must be a list")

    records = tuple(
        _parse_record(raw_record, root=root, role=role, schema_version=version)
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
    schema_version: int = 1,
) -> InventoryRecord:
    record = _require_mapping(raw_record, f"{role} record")
    record_id = _require_string(record.get("id"), f"{role} record id")

    fixture = _parse_fixture(
        _require_string(record.get("fixture"), f"{record_id} fixture"),
        _require_string(record.get("sha256"), f"{record_id} sha256"),
        root=root,
        record_id=record_id,
    )
    probe_filename_raw = record.get("probe_filename")
    probe_extension_raw = record.get("probe_extension")
    if probe_filename_raw is not None and probe_extension_raw is not None:
        raise InventoryValidationError(
            f"{record_id}: probe_extension and probe_filename are mutually exclusive"
        )
    if probe_filename_raw is not None:
        probe_extension = None
        probe_filename = _require_string(
            probe_filename_raw, f"{record_id} probe_filename"
        )
        if re.search(r"[/\\]|\.\.", probe_filename):
            raise InventoryValidationError(
                f"{record_id} probe_filename must not contain path separators"
            )
    elif record.get("probe_extension") is not None:
        probe_extension = _parse_extension(
            record.get("probe_extension"), f"{record_id} probe_extension"
        )
        probe_filename = None
    else:
        raise InventoryValidationError(
            f"{record_id}: exactly one of probe_extension or probe_filename must be set"
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

    if review.status == "verified" and probe_extension not in ground_truth.extensions:
        raise InventoryValidationError(
            f"verified record {record_id!r}: probe_extension "
            f"{probe_extension!r} must appear in ground_truth.extensions"
        )

    source_integrity = None
    format_validity = None
    ground_truth_evidence = None
    content_identifiability = None
    if schema_version >= 2:
        raw_source = record.get("source_integrity")
        if raw_source is not None:
            source_integrity = _parse_source_integrity(
                _require_mapping(raw_source, f"{record_id} source_integrity"),
                record_id=record_id,
            )
        raw_validity = record.get("format_validity")
        if raw_validity is not None:
            format_validity = _parse_format_validity(
                _require_mapping(raw_validity, f"{record_id} format_validity"),
                record_id=record_id,
            )
        raw_gt_evidence = record.get("ground_truth_evidence")
        if raw_gt_evidence is not None:
            ground_truth_evidence = _parse_gt_evidence(
                _require_mapping(raw_gt_evidence, f"{record_id} ground_truth_evidence"),
                record_id=record_id,
                claimed_mimes=ground_truth.mimes,
                claimed_extensions=ground_truth.extensions,
            )
        content_identifiability = _parse_identifiability(
            record.get("content_identifiability"),
            f"{record_id} content_identifiability",
        )
        if review.status == "verified" and role == "authoritative":
            problems: list[str] = []
            if source_integrity is None:
                problems.append("source_integrity missing")
            elif source_integrity.kind == "external" and (
                source_integrity.blob_sha1_verified is not True
            ):
                problems.append("source_integrity.blob_sha1_verified != true")
            if format_validity is None:
                problems.append("format_validity missing")
            elif format_validity.status != "verified":
                problems.append(f"format_validity.status={format_validity.status!r}")
            if ground_truth_evidence is None:
                problems.append("ground_truth_evidence missing")
            if problems:
                raise InventoryValidationError(
                    f"schema v2 verified record {record_id!r} fails truth axes: "
                    + "; ".join(problems)
                )
    return InventoryRecord(
        id=record_id,
        fixture=fixture,
        probe_extension=probe_extension,
        probe_filename=probe_filename,
        ground_truth=ground_truth,
        provenance=provenance,
        ground_truth_review=review,
        backends=backends,
        source_integrity=source_integrity,
        format_validity=format_validity,
        ground_truth_evidence=ground_truth_evidence,
        content_identifiability=content_identifiability,
    )


def _parse_gt_evidence(
    payload: Mapping[str, object],
    *,
    record_id: str,
    claimed_mimes: tuple[str, ...],
    claimed_extensions: tuple[str, ...],
) -> GroundTruthEvidence:
    """Validate the MIME/extension evidence axis (truth axis 3).

    Both directions are enforced: every claimed MIME and extension must have
    exactly one evidence entry with authority + URL reference, and no extra
    or duplicate claims are allowed.
    """

    def _require_claim_list(field: str) -> list[Mapping[str, object]]:
        value = payload.get(field)
        if not isinstance(value, list) or not value:
            raise InventoryValidationError(
                f"{record_id} ground_truth_evidence.{field} must be a non-empty list"
            )
        return [_require_mapping(c, f"{record_id} {field} claim") for c in value]

    mime_claims_payload = _require_claim_list("mime_claims")

    parsed_mime_claims: list[dict[str, str]] = []
    covered_mimes: set[str] = set()
    for claim in mime_claims_payload:
        mime_type = _require_string(
            claim.get("mime_type"), f"{record_id} claim mime_type"
        )
        authority = _require_string(
            claim.get("authority"), f"{record_id} claim authority"
        )
        reference = _require_string(
            claim.get("reference"), f"{record_id} claim reference"
        )
        if not (reference.startswith("http://") or reference.startswith("https://")):
            raise InventoryValidationError(
                f"{record_id} claim reference for {mime_type!r} must be a URL"
            )
        if mime_type in covered_mimes:
            raise InventoryValidationError(
                f"{record_id} has duplicate evidence claims for {mime_type!r}"
            )
        covered_mimes.add(mime_type)
        parsed_mime_claims.append(
            {"mime_type": mime_type, "authority": authority, "reference": reference}
        )

    uncovered_mimes = set(claimed_mimes) - covered_mimes
    extra_mimes = covered_mimes - set(claimed_mimes)
    if uncovered_mimes:
        raise InventoryValidationError(
            f"{record_id} evidence lacks MIME claims for: "
            + ", ".join(sorted(uncovered_mimes))
        )
    if extra_mimes:
        raise InventoryValidationError(
            f"{record_id} evidence has unclaimed MIME entries: "
            + ", ".join(sorted(extra_mimes))
        )

    extension_claims_payload = _require_claim_list("extension_claims")

    parsed_extension_claims: list[dict[str, str]] = []
    covered_extensions: set[str] = set()
    for claim in extension_claims_payload:
        ext = _require_string(claim.get("extension"), f"{record_id} claim extension")
        authority = _require_string(
            claim.get("authority"), f"{record_id} claim authority"
        )
        reference = _require_string(
            claim.get("reference"), f"{record_id} claim reference"
        )
        if not (reference.startswith("http://") or reference.startswith("https://")):
            raise InventoryValidationError(
                f"{record_id} claim reference for {ext!r} must be a URL"
            )
        if ext in covered_extensions:
            raise InventoryValidationError(
                f"{record_id} has duplicate evidence claims for {ext!r}"
            )
        covered_extensions.add(ext)
        parsed_extension_claims.append(
            {"extension": ext, "authority": authority, "reference": reference}
        )

    uncovered_exts = set(claimed_extensions) - covered_extensions
    extra_exts = covered_extensions - set(claimed_extensions)
    if uncovered_exts:
        raise InventoryValidationError(
            f"{record_id} evidence lacks extension claims for: "
            + ", ".join(sorted(uncovered_exts))
        )
    if extra_exts:
        raise InventoryValidationError(
            f"{record_id} evidence has unclaimed extension entries: "
            + ", ".join(sorted(extra_exts))
        )

    return GroundTruthEvidence(
        mime_claims=tuple(parsed_mime_claims),
        extension_claims=tuple(parsed_extension_claims),
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


def _parse_source_integrity(
    payload: Mapping[str, object],
    *,
    record_id: str,
) -> SourceIntegrity:
    kind = _require_string(payload.get("kind"), f"{record_id} source_integrity.kind")
    if kind not in ("external", "generated"):
        raise InventoryValidationError(
            f"{record_id} source_integrity.kind must be external or generated"
        )

    tier = payload.get("tier")
    if tier is not None:
        tier = _require_string(tier, f"{record_id} source_integrity.tier")
        if tier not in ("exact-byte", "pinned-sha-roundtrip"):
            raise InventoryValidationError(
                f"{record_id} source_integrity.tier is unsupported"
            )

    if kind == "external":
        origin_url = _require_string(
            payload.get("origin_url"), f"{record_id} source_integrity.origin_url"
        )
        origin_commit = _require_string(
            payload.get("origin_commit"), f"{record_id} source_integrity.origin_commit"
        )
        if not re.fullmatch(r"[0-9a-f]{40}", origin_commit):
            raise InventoryValidationError(
                f"{record_id} source_integrity.origin_commit must be a SHA-1"
            )
        blob_verified = payload.get("blob_sha1_verified")
        if blob_verified is not True:
            raise InventoryValidationError(
                f"{record_id} external source requires blob_sha1_verified=true"
            )
        return SourceIntegrity(
            kind=kind,
            origin_url=origin_url,
            origin_commit=origin_commit,
            blob_sha1_verified=True,
            tier=tier,
        )

    generator_symbol = _require_string(
        payload.get("generator_symbol"),
        f"{record_id} source_integrity.generator_symbol",
    )
    recipe_hash_value = payload.get("recipe_hash")
    recipe_hash = (
        None
        if recipe_hash_value is None
        else _require_string(
            recipe_hash_value, f"{record_id} source_integrity.recipe_hash"
        )
    )
    return SourceIntegrity(
        kind=kind,
        generator_symbol=generator_symbol,
        recipe_hash=recipe_hash,
        tier=tier,
    )


def _parse_format_validity(
    payload: Mapping[str, object],
    *,
    record_id: str,
) -> FormatValidity:
    status = _require_string(
        payload.get("status"), f"{record_id} format_validity.status"
    )
    if status not in ("verified", "needs_review", "failed"):
        raise InventoryValidationError(
            f"{record_id} format_validity.status is unsupported"
        )
    validator = _require_string(
        payload.get("validator"), f"{record_id} format_validity.validator"
    )
    evidence_payload = payload.get("evidence") or []
    evidence = tuple(
        _require_string(item, f"{record_id} format_validity.evidence")
        for item in evidence_payload
    )
    return FormatValidity(status=status, validator=validator, evidence=evidence)


_IDENTIFIABILITY_TIERS = frozenset(
    {"distinctive", "ambiguous", "generic-container", "not_applicable"}
)


def _parse_identifiability(value: object, field: str) -> str | None:
    if value is None:
        return None
    tier = _require_string(value, field)
    if tier not in _IDENTIFIABILITY_TIERS:
        raise InventoryValidationError(f"{field} is an unsupported quality tier")
    return tier


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
