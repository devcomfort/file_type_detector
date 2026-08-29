"""Tests for the conformance inventory review command line interface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from scripts.conformance.cli import main


def _write_legacy_truth(root: Path) -> Path:
    fixture_dir = root / "tests" / "fixtures"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "sample.bin").write_bytes(b"sample fixture")
    (fixture_dir / "other.txt").write_bytes(b"other fixture")

    source = root / "legacy_source.json"
    source.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "fixtures": [
                    {
                        "path": "tests/fixtures/sample.bin",
                        "canonical_mime": "application/x-test",
                        "canonical_extensions": [".bin"],
                        "category": "legacy",
                        "provenance": "Legacy source fixture",
                    },
                    {
                        "path": "tests/fixtures/other.txt",
                        "canonical_mime": "text/plain",
                        "canonical_extensions": [".txt"],
                        "category": "legacy",
                        "provenance": "Legacy text fixture",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return source


# Q. Does seed retain every legacy claim as an explicitly unreviewed candidate?
def test_seed_writes_all_legacy_records_as_needs_review(tmp_path: Path) -> None:
    source = _write_legacy_truth(tmp_path)
    candidates_path = tmp_path / "backend_inventory_candidates.json"

    # Seed and verify (the persisted candidates retain legacy claims without promotion)
    assert (
        main(
            [
                "seed",
                "--source",
                str(source),
                "--output",
                str(candidates_path),
                "--root",
                str(tmp_path),
            ]
        )
        == 0
    )
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))

    assert candidates["schema_version"] == 2
    assert [record["id"] for record in candidates["records"]] == [
        "sample-bin",
        "other-txt",
    ]
    assert candidates["records"][0] == {
        "id": "sample-bin",
        "fixture": "tests/fixtures/sample.bin",
        "sha256": hashlib.sha256(b"sample fixture").hexdigest(),
        "probe_extension": ".bin",
        "ground_truth": {
            "mime_types": ["application/x-test"],
            "extensions": [".bin"],
        },
        "provenance": "Legacy source fixture",
        "ground_truth_review": {
            "status": "needs_review",
            "reason": "Seeded from legacy canonical fixture data; independent Ground Truth review required",
        },
        "backends": ["lexical", "magic", "magika", "hybrid"],
    }


# Q. Does seed preserve distinct case-sensitive legacy fixture paths?
def test_seed_distinguishes_case_sensitive_fixture_names(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "tests" / "fixtures"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "sample.CBL").write_bytes(b"uppercase fixture")
    (fixture_dir / "sample.cbl").write_bytes(b"lowercase fixture")
    source = tmp_path / "legacy_source.json"
    source.write_text(
        json.dumps(
            {
                "fixtures": [
                    {
                        "path": "tests/fixtures/sample.CBL",
                        "canonical_mime": "text/x-cobol",
                        "canonical_extensions": [".cbl"],
                        "provenance": "Uppercase legacy fixture",
                    },
                    {
                        "path": "tests/fixtures/sample.cbl",
                        "canonical_mime": "text/x-cobol",
                        "canonical_extensions": [".cbl"],
                        "provenance": "Lowercase legacy fixture",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    candidates_path = tmp_path / "backend_inventory_candidates.json"

    # Seed and verify (case-sensitive paths must not collide before review)
    assert (
        main(
            [
                "seed",
                "--source",
                str(source),
                "--output",
                str(candidates_path),
                "--root",
                str(tmp_path),
            ]
        )
        == 0
    )

    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    assert [record["id"] for record in candidates["records"]] == [
        "sample-CBL",
        "sample-cbl",
    ]


# Q. Does seed disambiguate distinct names that share a readable identifier base?
def test_seed_disambiguates_punctuation_collisions(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "tests" / "fixtures"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "sample.c").write_bytes(b"c fixture")
    (fixture_dir / "sample.c++").write_bytes(b"c++ fixture")
    source = tmp_path / "legacy_source.json"
    source.write_text(
        json.dumps(
            {
                "fixtures": [
                    {
                        "path": "tests/fixtures/sample.c",
                        "canonical_mime": "text/x-c",
                        "canonical_extensions": [".c"],
                        "provenance": "C fixture",
                    },
                    {
                        "path": "tests/fixtures/sample.c++",
                        "canonical_mime": "text/x-c++",
                        "canonical_extensions": [".c++"],
                        "provenance": "C++ fixture",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    candidates_path = tmp_path / "backend_inventory_candidates.json"

    # Seed and verify (path-derived suffixes preserve both fixtures for review)
    assert (
        main(
            [
                "seed",
                "--source",
                str(source),
                "--output",
                str(candidates_path),
                "--root",
                str(tmp_path),
            ]
        )
        == 0
    )

    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    assert [record["id"] for record in candidates["records"]] == [
        "sample-c--" + hashlib.sha256(b"tests/fixtures/sample.c").hexdigest()[:12],
        "sample-c--" + hashlib.sha256(b"tests/fixtures/sample.c++").hexdigest()[:12],
    ]


# Q. Does review fail require-complete while any candidate remains unreviewed?
def test_review_requires_no_unresolved_candidates(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _write_legacy_truth(tmp_path)
    candidates_path = tmp_path / "backend_inventory_candidates.json"
    inventory_path = tmp_path / "backend_inventory.json"
    inventory_path.write_text(
        json.dumps({"schema_version": 2, "records": []}), encoding="utf-8"
    )
    main(
        [
            "seed",
            "--source",
            str(source),
            "--output",
            str(candidates_path),
            "--root",
            str(tmp_path),
        ]
    )

    # Review and verify (structured output exposes unresolved records before exit status 2)
    assert (
        main(
            [
                "review",
                "--candidates",
                str(candidates_path),
                "--inventory",
                str(inventory_path),
                "--root",
                str(tmp_path),
                "--require-complete",
            ]
        )
        == 2
    )
    summary = json.loads(capsys.readouterr().out)

    assert summary["candidate_count"] == 2
    assert summary["verified_count"] == 0
    assert summary["unresolved_count"] == 2


# Q. Does fix-extensions replace contradictory legacy aliases before promotion?
def test_promote_fix_extensions_replaces_conflicting_legacy_extensions(
    tmp_path: Path,
) -> None:
    source = _write_legacy_truth(tmp_path)
    candidates_path = tmp_path / "backend_inventory_candidates.json"
    inventory_path = tmp_path / "backend_inventory.json"
    inventory_path.write_text(
        json.dumps({"schema_version": 2, "records": []}), encoding="utf-8"
    )
    assert (
        main(
            [
                "seed",
                "--source",
                str(source),
                "--output",
                str(candidates_path),
                "--root",
                str(tmp_path),
            ]
        )
        == 0
    )
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    rec = candidates["records"][0]
    assert rec["id"] == "sample-bin"
    rec["ground_truth"]["extensions"] = [".txt", ".mp4"]
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")

    # Two-phase contract: --fix-extensions corrects aliases but does NOT promote.
    # Fixed records stay needs_review; a separate call with fresh evidence promotes.
    result = main(
        [
            "promote",
            "--candidates",
            str(candidates_path),
            "--inventory",
            str(inventory_path),
            "--root",
            str(tmp_path),
            "--reviewer",
            "fixture-reviewer",
            "--date",
            "2026-08-11",
            "--evidence",
            "format-spec.example",
            "--fix-extensions",
            "--ids",
            "sample-bin",
        ]
    )
    # sample-bin was fixed but NOT promoted (two-phase contract)
    updated = json.loads(candidates_path.read_text(encoding="utf-8"))
    fixed_rec = next(r for r in updated["records"] if r["id"] == "sample-bin")
    assert fixed_rec["ground_truth"]["extensions"] == [".bin"]
    assert fixed_rec["ground_truth_review"]["status"] == "needs_review"

    # Phase 2: add axes and mark verified, then promote
    from tests.conformance._inventory_factory import complete_v2_record

    axes = complete_v2_record(fixed_rec)
    fixed_rec["source_integrity"] = axes["source_integrity"]
    fixed_rec["format_validity"] = axes["format_validity"]
    fixed_rec["ground_truth_evidence"] = axes["ground_truth_evidence"]
    candidates_path.write_text(json.dumps(updated), encoding="utf-8")

    assert (
        main(
            [
                "promote",
                "--candidates",
                str(candidates_path),
                "--inventory",
                str(inventory_path),
                "--root",
                str(tmp_path),
                "--reviewer",
                "fixture-reviewer",
                "--date",
                "2026-08-11",
                "--evidence",
                "format-spec.example",
                "--ids",
                "sample-bin",
            ]
        )
        == 0
    )

    promoted_inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert len(promoted_inventory["records"]) == 1
    assert promoted_inventory["records"][0]["id"] == "sample-bin"
    assert promoted_inventory["records"][0]["ground_truth"]["extensions"] == [".bin"]


# Q. Does promote leave files untouched when pre-write validation fails?
def test_promote_atomic_on_missing_axes(tmp_path: Path) -> None:
    source = _write_legacy_truth(tmp_path)
    candidates_path = tmp_path / "backend_inventory_candidates.json"
    inventory_path = tmp_path / "backend_inventory.json"
    inventory_path.write_text(
        json.dumps({"schema_version": 2, "records": []}), encoding="utf-8"
    )
    main(
        [
            "seed",
            "--source",
            str(source),
            "--output",
            str(candidates_path),
            "--root",
            str(tmp_path),
        ]
    )
    candidates_before = candidates_path.read_bytes()
    inventory_before = inventory_path.read_bytes()

    with pytest.raises(SystemExit):
        main(
            [
                "promote",
                "--candidates",
                str(candidates_path),
                "--inventory",
                str(inventory_path),
                "--root",
                str(tmp_path),
                "--reviewer",
                "test",
                "--date",
                "2026-08-24",
                "--evidence",
                "https://example.test",
            ]
        )

    assert candidates_path.read_bytes() == candidates_before
    assert inventory_path.read_bytes() == inventory_before


# Q. Does promote leave files untouched when evidence has extra MIME claims?
def test_promote_atomic_on_extra_evidence_claims(tmp_path: Path) -> None:
    source = _write_legacy_truth(tmp_path)
    candidates_path = tmp_path / "backend_inventory_candidates.json"
    inventory_path = tmp_path / "backend_inventory.json"
    inventory_path.write_text(
        json.dumps({"schema_version": 2, "records": []}), encoding="utf-8"
    )
    main(
        [
            "seed",
            "--source",
            str(source),
            "--output",
            str(candidates_path),
            "--root",
            str(tmp_path),
        ]
    )

    # Add axes with an extra MIME claim not present in GT
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    rec = candidates["records"][0]
    from tests.conformance._inventory_factory import complete_v2_record

    axes = complete_v2_record(rec)
    rec["source_integrity"] = axes["source_integrity"]
    rec["format_validity"] = axes["format_validity"]
    rec["ground_truth_evidence"] = axes["ground_truth_evidence"]
    rec["ground_truth_evidence"]["mime_claims"].append(
        {
            "mime_type": "application/x-fabricated-extra",
            "authority": "fabricated source",
            "reference": "https://fake.example/extra",
        }
    )
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")

    cand_before = candidates_path.read_bytes()
    inv_before = inventory_path.read_bytes()

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "promote",
                "--candidates",
                str(candidates_path),
                "--inventory",
                str(inventory_path),
                "--root",
                str(tmp_path),
                "--reviewer",
                "test",
                "--date",
                "2026-08-24",
                "--evidence",
                "https://example.test",
                "--ids",
                "sample-bin",
            ]
        )
    assert exc_info.value.code == 2

    assert candidates_path.read_bytes() == cand_before
    assert inventory_path.read_bytes() == inv_before


# Q. Does promotion preserve a filename-only verified record without a fake extension?
def test_promote_filename_only_record(tmp_path: Path) -> None:
    fixture = tmp_path / "Gemfile"
    fixture.write_text('source "https://rubygems.org"\n', encoding="utf-8")
    digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
    candidates_path = tmp_path / "candidates.json"
    inventory_path = tmp_path / "inventory.json"
    record = {
        "id": "sample-gemfile",
        "fixture": "Gemfile",
        "sha256": digest,
        "probe_filename": "Gemfile",
        "ground_truth": {"mime_types": ["text/plain"], "extensions": [], "filenames": ["Gemfile"]},
        "provenance": "filename-only fixture",
        "ground_truth_review": {"status": "excluded", "reason": "awaiting review"},
        "backends": ["lexical", "magic", "magika", "hybrid"],
        "source_integrity": {"kind": "generated", "generator_symbol": "test", "recipe_hash": "a" * 64, "tier": "exact-byte"},
        "format_validity": {"status": "verified", "validator": "test-validator", "evidence": ["syntax"]},
        "content_identifiability": "distinctive",
        "ground_truth_evidence": {
            "mime_claims": [{"mime_type": "text/plain", "authority": "IANA", "reference": "https://www.iana.org/assignments/media-types/media-types.xhtml"}],
            "filename_claims": [{"filename": "Gemfile", "authority": "Bundler", "reference": "https://bundler.io/guides/gemfile.html"}],
        },
    }
    payload = {"schema_version": 2, "records": [record]}
    candidates_path.write_text(json.dumps(payload), encoding="utf-8")
    inventory_path.write_text(json.dumps({"schema_version": 2, "records": []}), encoding="utf-8")
    assert main(["promote", "--candidates", str(candidates_path), "--inventory", str(inventory_path), "--root", str(tmp_path), "--ids", "sample-gemfile", "--reviewer", "automated-independent-validator", "--date", "2026-08-29", "--evidence", "test-validator"]) == 0
    promoted = json.loads(inventory_path.read_text(encoding="utf-8"))["records"][0]
    assert promoted["probe_filename"] == "Gemfile"
    assert "probe_extension" not in promoted
    assert promoted["ground_truth"]["extensions"] == []
    assert promoted["ground_truth"]["filenames"] == ["Gemfile"]
