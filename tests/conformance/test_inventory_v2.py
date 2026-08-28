"""Tests for the schema v2 four-axis inventory extension."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from scripts.conformance.inventory import (
    InventoryValidationError,
    _load_document,
)

_GT_EVIDENCE = {
    "mime_claims": [
        {
            "mime_type": "application/x-test",
            "authority": "example-test-registry",
            "reference": "https://registry.example.test/application-x-test",
        }
    ],
    "extension_claims": [
        {
            "extension": ".bin",
            "authority": "example-test-registry",
            "reference": "https://registry.example.test/bin-extension",
        }
    ],
}


def _v2_record(fixture: Path, **overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": "fixture-bin",
        "fixture": fixture.name,
        "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "probe_extension": ".bin",
        "ground_truth": {
            "mime_types": ["application/x-test"],
            "extensions": [".bin"],
        },
        "provenance": "Fixture created for schema v2 validation",
        "ground_truth_review": {
            "status": "verified",
            "reviewed_by": "test-reviewer",
            "reviewed_at": "2026-08-24",
            "evidence": ["https://example.test/fixture-bin"],
        },
        "backends": ["lexical", "magic", "magika", "hybrid"],
        "source_integrity": {
            "kind": "generated",
            "generator_symbol": "scripts.generators.base.BaseGenerator",
            "recipe_hash": "a" * 64,
            "tier": "exact-byte",
        },
        "format_validity": {
            "status": "verified",
            "validator": "stdlib-structural-check/1.0",
            "evidence": ["round-trip ok"],
        },
        "ground_truth_evidence": _GT_EVIDENCE,
        "content_identifiability": "distinctive",
    }
    record.update(overrides)
    return record


def _write(tmp_path: Path, records: list[dict[str, object]]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({"schema_version": 2, "records": records}))
    return path


# Q. Does a complete v2 verified record parse all four axes?
def test_parses_complete_v2_record(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    path = _write(tmp_path, [_v2_record(fixture)])

    records = _load_document(path, root=tmp_path, role="authoritative")

    assert records[0].source_integrity is not None
    assert records[0].source_integrity.kind == "generated"
    assert records[0].source_integrity.tier == "exact-byte"
    assert records[0].format_validity is not None
    assert records[0].format_validity.status == "verified"
    assert records[0].ground_truth_evidence is not None
    assert records[0].content_identifiability == "distinctive"


# Q. Is a v2 verified authoritative record rejected when a truth axis is missing?
def test_rejects_v2_verified_without_truth_axes(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(fixture)
    del record["source_integrity"]
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="source_integrity missing"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Is an external source without verified blob SHA rejected?
def test_rejects_external_source_without_blob_verification(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(
        fixture,
        source_integrity={
            "kind": "external",
            "origin_url": "https://raw.test/repo/commit/x/sample.bin",
            "origin_commit": "b" * 40,
            "blob_sha1_verified": False,
        },
    )
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="blob_sha1_verified"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Is format_validity=failed rejected on a v2 verified record?
def test_rejects_verified_record_with_failed_validity(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(
        fixture,
        format_validity={
            "status": "failed",
            "validator": "stdlib-structural-check/1.0",
        },
    )
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="format_validity.status"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Is an unsupported identifiability tier rejected?
def test_rejects_unknown_identifiability_tier(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(fixture, content_identifiability="easy")
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="quality tier"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Are GT MIME claims without evidence entries rejected?
def test_rejects_gt_mime_claim_without_evidence(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(fixture)
    record["ground_truth"] = {
        "mime_types": ["application/x-test", "application/x-extra"],
        "extensions": [".bin"],
    }
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="lacks MIME claims"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Are extension claims without evidence entries rejected (.tgz-style aliases)?
def test_rejects_extension_alias_without_evidence(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(fixture)
    record["ground_truth"] = {
        "mime_types": ["application/x-test"],
        "extensions": [".bin", ".tgz"],
    }
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="lacks extension claims"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Do needs_review candidates load without truth axes (active review queue)?
def test_needs_review_candidate_loads_without_axes(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(fixture)
    record["id"] = "fixture-review"
    record["ground_truth_review"] = {
        "status": "needs_review",
        "reason": "MIME evidence gathering in progress",
    }
    for field in (
        "source_integrity",
        "format_validity",
        "ground_truth_evidence",
        "content_identifiability",
    ):
        del record[field]
    path = _write(tmp_path, [record])

    records = _load_document(path, root=tmp_path, role="candidate")
    assert records[0].source_integrity is None


# Q. Are duplicate evidence claims rejected?
def test_rejects_duplicate_evidence_claims(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(fixture)
    record["ground_truth_evidence"] = {
        "mime_claims": [
            {
                "mime_type": "application/x-test",
                "authority": "a",
                "reference": "https://r.test/1",
            },
            {
                "mime_type": "application/x-test",
                "authority": "b",
                "reference": "https://r.test/2",
            },
        ],
        "extension_claims": _GT_EVIDENCE["extension_claims"],
    }
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="duplicate evidence claims"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Is setting both probe_extension and probe_filename rejected?
def test_rejects_both_probe_set(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(
        fixture,
        probe_filename="Gemfile",
    )
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="mutually exclusive"):
        _load_document(path, root=tmp_path, role="authoritative")


# Q. Is neither probe_extension nor probe_filename rejected?
def test_rejects_neither_probe_set(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"fixture bytes")
    record = _v2_record(fixture)
    record.pop("probe_extension")
    # _v2_record has no probe_filename by default
    path = _write(tmp_path, [record])

    with pytest.raises(InventoryValidationError, match="exactly one"):
        _load_document(path, root=tmp_path, role="candidate")


# Q. Is a verified filename-based record loaded with probe_filename, empty extensions, and filename_claims?
def test_valid_filename_record_loads(tmp_path: Path) -> None:
    fixture = tmp_path / "Gemfile"
    fixture.write_bytes(b'source "https://rubygems.org"\ngem "rake"\n')
    record = _v2_record(fixture)
    del record["probe_extension"]
    record["probe_filename"] = "Gemfile"
    record["ground_truth"] = {
        "mime_types": ["text/plain"],
        "extensions": [],
        "filenames": ["Gemfile"],
    }
    record["ground_truth_evidence"] = {
        "mime_claims": [
            {
                "mime_type": "text/plain",
                "authority": "iana-media-types",
                "reference": "https://www.iana.org/assignments/media-types/text/plain",
            }
        ],
        "filename_claims": [
            {
                "filename": "Gemfile",
                "authority": "bundler-docs",
                "reference": "https://bundler.io/docs/gemfile.html",
            }
        ],
    }
    path = _write(tmp_path, [record])

    records = _load_document(path, root=tmp_path, role="candidate")
    assert len(records) == 1
    assert records[0].probe_filename == "Gemfile"
    assert records[0].probe_extension is None
    assert records[0].ground_truth.filenames == ("Gemfile",)
    assert records[0].ground_truth.extensions == ()


# Q. Does verified filename validation reject mismatched filename or missing claims?
def test_verified_filename_record_invariant_rejections(tmp_path: Path) -> None:
    fixture = tmp_path / "Gemfile"
    fixture.write_bytes(b'source "https://rubygems.org"\n')

    # 1. probe_filename not in ground_truth.filenames
    rec1 = _v2_record(fixture)
    del rec1["probe_extension"]
    rec1["probe_filename"] = "Gemfile"
    rec1["ground_truth"] = {
        "mime_types": ["text/plain"],
        "extensions": [],
        "filenames": ["Rakefile"],
    }
    rec1["ground_truth_evidence"] = {
        "mime_claims": [
            {
                "mime_type": "text/plain",
                "authority": "iana",
                "reference": "https://www.iana.org/assignments/media-types/text/plain",
            }
        ],
        "filename_claims": [
            {
                "filename": "Rakefile",
                "authority": "rake",
                "reference": "https://github.com/ruby/rake",
            }
        ],
    }
    path1 = _write(tmp_path / "d1", [rec1])
    with pytest.raises(InventoryValidationError, match="must appear in ground_truth.filenames"):
        _load_document(path1, root=tmp_path, role="candidate")

    # 2. filename_claims missing for claimed filename
    rec2 = _v2_record(fixture)
    del rec2["probe_extension"]
    rec2["probe_filename"] = "Gemfile"
    rec2["ground_truth"] = {
        "mime_types": ["text/plain"],
        "extensions": [],
        "filenames": ["Gemfile"],
    }
    rec2["ground_truth_evidence"] = {
        "mime_claims": [
            {
                "mime_type": "text/plain",
                "authority": "iana",
                "reference": "https://www.iana.org/assignments/media-types/text/plain",
            }
        ],
    }
    path2 = _write(tmp_path / "d2", [rec2])
    with pytest.raises(InventoryValidationError, match="ground_truth_evidence.filename_claims must be a non-empty list"):
        _load_document(path2, root=tmp_path, role="candidate")
