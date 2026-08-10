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

    source = root / "canonical_fixtures.json"
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

    assert candidates["schema_version"] == 1
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
    source = tmp_path / "canonical_fixtures.json"
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
    source = tmp_path / "canonical_fixtures.json"
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
        json.dumps({"schema_version": 1, "records": []}), encoding="utf-8"
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
        json.dumps({"schema_version": 1, "records": []}), encoding="utf-8"
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
    candidates["records"][0]["ground_truth"]["extensions"] = [".txt", ".mp4"]
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")

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
                "--fix-extensions",
                "--all-clean",
            ]
        )
        == 0
    )

    promoted_candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    promoted_inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert promoted_candidates["records"][0]["ground_truth"]["extensions"] == [".bin"]
    assert promoted_inventory["records"][0]["ground_truth"]["extensions"] == [".bin"]
