"""Tests for independently reviewed conformance inventory records."""

from __future__ import annotations

from copy import deepcopy

import hashlib
import json
from pathlib import Path
import pytest

from scripts.conformance.inventory import (
    InventoryValidationError,
    load_verified_inventory,
    review_summary,
)


def _verified_record(fixture: Path) -> dict[str, object]:
    return {
        "id": "fixture-bin",
        "fixture": fixture.name,
        "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "probe_extension": ".bin",
        "ground_truth": {
            "mime_types": ["application/x-test"],
            "extensions": [".bin"],
        },
        "provenance": "Fixture created for inventory validation",
        "ground_truth_review": {
            "status": "verified",
            "reviewed_by": "test-reviewer",
            "reviewed_at": "2026-07-21",
            "evidence": ["https://example.test/fixture-bin"],
        },
        "backends": ["lexical", "magic", "magika", "hybrid"],
    }


# Q. Does a byte-verified authoritative record load only when an identical candidate is reviewed?
def test_loads_fact_identical_verified_record(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _verified_record(fixture)
    candidates_path = tmp_path / "candidates.json"
    inventory_path = tmp_path / "inventory.json"
    candidates_path.write_text(json.dumps({"schema_version": 1, "records": [record]}))
    inventory_path.write_text(json.dumps({"schema_version": 1, "records": [record]}))

    # Load and verify (the returned record must retain independently reviewed facts)
    records = load_verified_inventory(candidates_path, inventory_path, root=tmp_path)

    assert [record.id for record in records] == ["fixture-bin"]
    assert records[0].ground_truth.mimes == ("application/x-test",)


# Q. Is a verified candidate rejected when no fact-identical authoritative record includes it?
def test_rejects_verified_candidate_without_authoritative_record(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    candidate = _verified_record(fixture)
    candidates_path, inventory_path = _write_pair(tmp_path, [candidate], [])

    # Load and verify (reviewed candidates cannot disappear before collection)
    with pytest.raises(
        InventoryValidationError, match="requires an authoritative record"
    ):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)


def _needs_review_record(
    fixture: Path, record_id: str, legacy_extension: str
) -> dict[str, object]:
    return {
        "id": record_id,
        "fixture": fixture.name,
        "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "probe_extension": fixture.suffix,
        "ground_truth": {
            "mime_types": ["application/x-test"],
            "extensions": [legacy_extension],
        },
        "provenance": "Legacy declaration awaiting independent review",
        "ground_truth_review": {
            "status": "needs_review",
            "reason": "Filename suffix conflicts with legacy declared extension",
        },
        "backends": ["lexical", "magic", "magika", "hybrid"],
    }


# Q. Are contradictory legacy `.aiff` and `.avif` candidates reported but omitted from observations?
def test_reports_unresolved_legacy_extension_conflicts(tmp_path: Path) -> None:
    aiff = tmp_path / "sample.aiff"
    avif = tmp_path / "sample.avif"
    aiff.write_bytes(b"aiff fixture")
    avif.write_bytes(b"avif fixture")
    candidates = {
        "schema_version": 1,
        "records": [
            _needs_review_record(aiff, "sample-aiff", ".txt"),
            _needs_review_record(avif, "sample-avif", ".mp4"),
        ],
    }
    candidates_path = tmp_path / "candidates.json"
    inventory_path = tmp_path / "inventory.json"
    candidates_path.write_text(json.dumps(candidates))
    inventory_path.write_text(json.dumps({"schema_version": 1, "records": []}))

    # Summarize and verify (only unresolved records appear, with their proposed extensions)
    summary = review_summary(candidates_path, inventory_path, root=tmp_path)

    assert summary["candidate_count"] == 2
    assert summary["verified_count"] == 0
    assert summary["unresolved_count"] == 2
    assert summary["candidate_suffix_count"] == 2
    assert summary["verified_suffix_count"] == 0
    assert summary["unresolved_suffix_count"] == 2
    assert summary["excluded_count"] == 0
    assert summary["excluded_suffix_count"] == 0
    assert summary["unresolved"] == [
        {
            "id": "sample-aiff",
            "reason": "Filename suffix conflicts with legacy declared extension",
            "provenance": "Legacy declaration awaiting independent review",
            "mimes": ["application/x-test"],
            "extensions": [".txt"],
        },
        {
            "id": "sample-avif",
            "reason": "Filename suffix conflicts with legacy declared extension",
            "provenance": "Legacy declaration awaiting independent review",
            "mimes": ["application/x-test"],
            "extensions": [".mp4"],
        },
    ]


# Q. Do noncanonical legacy claims remain reportable until independent review resolves them?
def test_reports_noncanonical_legacy_claims_pending_review(tmp_path: Path) -> None:
    fixture = tmp_path / "sample.R"
    fixture.write_bytes(b"legacy R fixture")
    candidate = _needs_review_record(fixture, "sample-R", ".R")
    candidate["probe_extension"] = ".r"
    candidate["ground_truth"] = {
        "mime_types": ["application/CDFV2"],
        "extensions": [".R"],
    }
    candidates_path, inventory_path = _write_pair(tmp_path, [candidate], [])

    # Summarize and verify (raw legacy claims stay visible without becoming facts)
    summary = review_summary(candidates_path, inventory_path, root=tmp_path)

    assert summary["unresolved"] == [
        {
            "id": "sample-R",
            "reason": "Filename suffix conflicts with legacy declared extension",
            "provenance": "Legacy declaration awaiting independent review",
            "mimes": ["application/CDFV2"],
            "extensions": [".R"],
        },
    ]


def _write_pair(
    tmp_path: Path,
    candidates: list[dict[str, object]],
    authoritative: list[dict[str, object]],
) -> tuple[Path, Path]:
    candidates_path = tmp_path / "candidates.json"
    inventory_path = tmp_path / "inventory.json"
    candidates_path.write_text(json.dumps({"schema_version": 1, "records": candidates}))
    inventory_path.write_text(
        json.dumps({"schema_version": 1, "records": authoritative})
    )
    return candidates_path, inventory_path


# Q. Is an authoritative record rejected when its candidate has not completed review?
def test_rejects_authoritative_record_without_verified_candidate(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "sample.aiff"
    fixture.write_bytes(b"aiff fixture")
    candidate = _needs_review_record(fixture, "sample-aiff", ".txt")
    authoritative = deepcopy(candidate)
    authoritative["ground_truth_review"] = {
        "status": "verified",
        "reviewed_by": "test-reviewer",
        "reviewed_at": "2026-07-21",
        "evidence": ["https://example.test/sample-aiff"],
    }
    candidates_path, inventory_path = _write_pair(
        tmp_path, [candidate], [authoritative]
    )

    # Load and verify (the review status, not detector output, blocks promotion)
    with pytest.raises(InventoryValidationError, match="requires a verified candidate"):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)


# Q. Does an authoritative record itself require completed independent review?
def test_rejects_authoritative_record_with_unverified_review(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    candidate = _needs_review_record(fixture, "fixture-bin", ".bin")
    candidates_path, inventory_path = _write_pair(tmp_path, [candidate], [candidate])

    # Load and verify (authoritative data cannot carry unresolved review state)
    with pytest.raises(InventoryValidationError, match="requires verified review"):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)


# Q. Does the schema reject an unsupported review status before a record is used?
def test_rejects_unsupported_review_status(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    candidate = _verified_record(fixture)
    candidate["ground_truth_review"] = {"status": "unreviewed"}
    candidates_path, inventory_path = _write_pair(tmp_path, [candidate], [])

    # Load and verify (unknown statuses cannot become an implicit review state)
    with pytest.raises(InventoryValidationError, match="unsupported"):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)


# Q. Does an uppercase declared extension fail rather than normalize into a different Ground Truth claim?
def test_rejects_noncanonical_extension_case(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    candidate = _verified_record(fixture)
    ground_truth = deepcopy(candidate["ground_truth"])
    ground_truth["extensions"] = [".BIN"]
    candidate["ground_truth"] = ground_truth
    candidates_path, inventory_path = _write_pair(tmp_path, [candidate], [])

    # Load and verify (review data must already be canonical)
    with pytest.raises(InventoryValidationError, match="lowercase"):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)


# Q. Does a verified review require evidence rather than relying on its fixture checksum?
def test_rejects_verified_record_without_evidence(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    candidate = _verified_record(fixture)
    review = deepcopy(candidate["ground_truth_review"])
    review.pop("evidence")
    candidate["ground_truth_review"] = review
    candidates_path, inventory_path = _write_pair(tmp_path, [candidate], [])

    # Load and verify (a byte digest cannot substitute for independent evidence)
    with pytest.raises(
        InventoryValidationError, match="requires reviewer, date, and evidence"
    ):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)


# Q. Does a changed fixture byte sequence fail before Ground Truth reaches collection?
def test_rejects_fixture_digest_mismatch(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    candidate = _verified_record(fixture)
    fixture.write_bytes(b"changed fixture bytes")
    candidates_path, inventory_path = _write_pair(tmp_path, [candidate], [])

    # Load and verify (the digest protects fixture identity, not MIME correctness)
    with pytest.raises(InventoryValidationError, match="digest mismatch"):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)


# Q. Are duplicate candidate identifiers rejected before pair validation?
def test_rejects_duplicate_candidate_identifier(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    candidate = _verified_record(fixture)
    candidates_path, inventory_path = _write_pair(
        tmp_path,
        [candidate, deepcopy(candidate)],
        [],
    )

    # Load and verify (record identity must remain unambiguous for review history)
    with pytest.raises(InventoryValidationError, match="duplicate record ids"):
        load_verified_inventory(candidates_path, inventory_path, root=tmp_path)
