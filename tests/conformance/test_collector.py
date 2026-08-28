"""Tests for fresh-process backend conformance collection."""

from __future__ import annotations

import json
import subprocess
import sys
from hashlib import sha256
import pytest
from types import ModuleType
from pathlib import Path

from scripts.conformance.collector import collect_observation
from scripts.conformance.types import (
    FixtureReference,
    GroundTruth,
    GroundTruthReview,
    InventoryRecord,
)


def _record(
    *,
    fixture: str,
    probe_extension: str = ".probe",
    digest: str = "0" * 64,
) -> InventoryRecord:
    return InventoryRecord(
        id="sample",
        fixture=FixtureReference(path=fixture, sha256=digest),
        probe_extension=probe_extension,
        ground_truth=GroundTruth(mimes=("text/plain",), extensions=(probe_extension,)),
        provenance="test fixture",
        ground_truth_review=GroundTruthReview(
            status="verified",
            reviewed_by="reviewer",
            reviewed_at="2026-07-21",
            evidence=("test evidence",),
            reason=None,
        ),
        backends=("lexical",),
    )


def test_stage_probe_copies_bytes_to_declared_suffix_and_cleans_up(
    tmp_path: Path,
) -> None:
    from scripts.conformance.collector import stage_probe

    fixture_bytes = b"reviewed fixture bytes"
    fixture = tmp_path / "fixtures" / "source.bin"
    fixture.parent.mkdir()
    fixture.write_bytes(fixture_bytes)
    record = _record(
        fixture="fixtures/source.bin",
        digest=sha256(fixture_bytes).hexdigest(),
    )

    with stage_probe(record, root=tmp_path) as probe:
        staging_directory = probe.parent
        assert probe.suffix == ".probe"
        assert probe.read_bytes() == fixture.read_bytes()
        assert probe.exists()

    assert not staging_directory.exists()


def test_semantic_output_lowercases_deduplicates_and_sorts() -> None:
    from scripts.conformance.evaluator import semantic_output

    assert semantic_output(
        mime_types=("TEXT/PLAIN", "text/plain", "application/json"),
        extensions=("txt", ".json", ".txt"),
    ) == {
        "mime_types": ["application/json", "text/plain"],
        "extensions": [".json", ".txt"],
    }


def test_stage_probe_rejects_bytes_that_do_not_match_reviewed_digest(
    tmp_path: Path,
) -> None:
    from scripts.conformance.collector import stage_probe

    fixture = tmp_path / "fixtures" / "source.bin"
    fixture.parent.mkdir()
    fixture.write_bytes(b"changed bytes")

    with pytest.raises(ValueError, match="staged probe digest"):
        with stage_probe(_record(fixture="fixtures/source.bin"), root=tmp_path):
            pass


def test_evaluate_output_requires_both_ground_truth_intersections() -> None:
    from scripts.conformance.evaluator import evaluate_output

    result = evaluate_output(
        semantic={"mime_types": ["text/plain"], "extensions": [".txt"]},
        ground_truth=GroundTruth(
            mimes=("text/plain", "text/x-readme"),
            extensions=(".md", ".txt"),
        ),
        status="ok",
    )

    assert result == {
        "mime_match": True,
        "extension_match": True,
        "overall_match": True,
        "match_level": "exact",
    }


def test_evaluate_output_marks_non_results_and_errors_as_mismatches() -> None:
    from scripts.conformance.evaluator import evaluate_output

    truth = GroundTruth(mimes=("text/plain",), extensions=(".txt",))

    for status in ("no_result", "error"):
        assert evaluate_output(
            semantic={"mime_types": ["text/plain"], "extensions": [".txt"]},
            ground_truth=truth,
            status=status,
        ) == {
            "mime_match": False,
            "extension_match": False,
            "overall_match": False,
            "match_level": "miss",
        }


def _write_reviewed_inventory(root: Path) -> tuple[Path, Path]:
    fixture = root / "fixtures" / "source.bin"
    fixture.parent.mkdir()
    fixture_bytes = b"backend conformance fixture"
    fixture.write_bytes(fixture_bytes)
    record = {
        "id": "sample",
        "fixture": "fixtures/source.bin",
        "sha256": sha256(fixture_bytes).hexdigest(),
        "probe_extension": ".txt",
        "ground_truth": {
            "mime_types": ["text/plain"],
            "extensions": [".txt"],
        },
        "provenance": "test fixture",
        "ground_truth_review": {
            "status": "verified",
            "reviewed_by": "reviewer",
            "reviewed_at": "2026-07-21",
            "evidence": ["test evidence"],
        },
        "backends": ["lexical", "magic", "magika", "hybrid"],
    }
    from tests.conformance._inventory_factory import complete_v2_record

    record = complete_v2_record(record)
    candidates = root / "candidates.json"
    inventory = root / "inventory.json"
    payload = {"schema_version": 2, "records": [record]}
    candidates.write_text(json.dumps(payload), encoding="utf-8")
    inventory.write_text(json.dumps(payload), encoding="utf-8")
    return candidates, inventory


def test_collect_command_uses_fresh_worker_and_writes_observations(
    monkeypatch, tmp_path: Path
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output = tmp_path / "observations.json"
    repository_root = Path(__file__).parents[2]
    monkeypatch.setenv(
        "LIBMAGIC_DISTRIBUTION",
        "python-magic-bin==0.4.14",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.conformance.collector",
            "collect",
            "--candidates",
            str(candidates),
            "--inventory",
            str(inventory),
            "--output",
            str(output),
            "--root",
            str(tmp_path),
            "--runner-label",
            "test-runner",
        ],
        check=True,
        cwd=repository_root,
        capture_output=True,
        text=True,
    )

    assert completed.stderr == ""
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["inventory_sha256"] == sha256(inventory.read_bytes()).hexdigest()
    assert [item["backend"] for item in payload["observations"]] == [
        "lexical",
        "magic",
        "magika",
        "hybrid",
    ]
    lexical = payload["observations"][0]
    assert lexical["inventory_id"] == "sample"
    assert lexical["status"] == "ok"
    assert lexical["raw_output"] == {
        "mime_types": ["text/plain"],
        "extensions": [".txt"],
    }
    assert lexical["semantic_output"] == lexical["raw_output"]
    assert lexical["evaluation"] == {
        "mime_match": True,
        "extension_match": True,
        "overall_match": True,
        "match_level": "exact",
    }
    assert lexical["platform"]["runner_label"] == "test-runner"
    assert set(lexical["runtime"]) == {
        "python",
        "filetype_detector",
        "python_magic",
        "libmagic",
        "libmagic_distribution",
        "magika",
        "magika_model",
    }
    assert lexical["runtime"]["libmagic_distribution"] == "python-magic-bin==0.4.14"


# Q. Can a local collection remain schema-valid without CI dependency metadata?
def test_runtime_info_uses_null_distribution_outside_ci(monkeypatch) -> None:
    from scripts.conformance import collector

    monkeypatch.delenv("LIBMAGIC_DISTRIBUTION", raising=False)

    assert collector._runtime_info()["libmagic_distribution"] is None


def test_collect_observation_preserves_backend_failure_without_fallback(
    monkeypatch, tmp_path: Path
) -> None:
    from scripts.conformance import collector

    fixture = tmp_path / "fixtures" / "source.bin"
    fixture.parent.mkdir()
    fixture_bytes = b"reviewed fixture bytes"
    fixture.write_bytes(fixture_bytes)
    record = _record(
        fixture="fixtures/source.bin",
        probe_extension=".txt",
        digest=sha256(fixture_bytes).hexdigest(),
    )
    requested_backends: list[str] = []

    class FailingInferencer:
        def infer(self, path: Path) -> object:
            raise RuntimeError("native backend unavailable")

    def failing_backend(name: str) -> FailingInferencer:
        requested_backends.append(name)
        return FailingInferencer()

    monkeypatch.setattr(collector, "_inferencer_for_backend", failing_backend)

    observation = collector.collect_observation(
        record,
        backend="lexical",
        root=tmp_path,
        runner_label="test-runner",
    )

    assert requested_backends == ["lexical"]
    assert observation["status"] == "error"
    assert observation["error"] == {
        "type": "RuntimeError",
        "message": "native backend unavailable",
    }
    assert observation["raw_output"] is None
    assert observation["semantic_output"] is None
    assert observation["evaluation"] == {
        "mime_match": False,
        "extension_match": False,
        "overall_match": False,
        "match_level": "miss",
    }


def test_collect_observation_classifies_empty_output_as_no_result(
    monkeypatch, tmp_path: Path
) -> None:
    from filetype_detector.core import FileType
    from scripts.conformance import collector

    fixture = tmp_path / "fixtures" / "source.bin"
    fixture.parent.mkdir()
    fixture_bytes = b"reviewed fixture bytes"
    fixture.write_bytes(fixture_bytes)
    record = _record(
        fixture="fixtures/source.bin",
        probe_extension=".txt",
        digest=sha256(fixture_bytes).hexdigest(),
    )

    class EmptyInferencer:
        def infer(self, path: Path) -> FileType:
            return FileType()

    monkeypatch.setattr(
        collector, "_inferencer_for_backend", lambda name: EmptyInferencer()
    )

    observation = collector.collect_observation(
        record,
        backend="lexical",
        root=tmp_path,
        runner_label="test-runner",
    )

    assert observation["status"] == "no_result"
    assert observation["raw_output"] == {"mime_types": [], "extensions": []}
    assert observation["semantic_output"] == {"mime_types": [], "extensions": []}
    assert observation["evaluation"] == {
        "mime_match": False,
        "extension_match": False,
        "overall_match": False,
        "match_level": "miss",
    }


def test_magika_versions_preserve_available_module_metadata(monkeypatch) -> None:
    from scripts.conformance.collector import _magika_versions

    module = ModuleType("magika")

    class Magika:
        def get_module_version(self) -> str:
            return "test-module-version"

    module.Magika = Magika
    monkeypatch.setitem(sys.modules, "magika", module)

    assert _magika_versions() == ("test-module-version", None)


def test_collect_command_rejects_blank_runner_label(tmp_path: Path) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output = tmp_path / "observations.json"
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.conformance.collector",
            "collect",
            "--candidates",
            str(candidates),
            "--inventory",
            str(inventory),
            "--output",
            str(output),
            "--root",
            str(tmp_path),
            "--runner-label",
            "   ",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "runner label must be non-empty" in completed.stderr
    assert not output.exists()


def test_collect_command_rejects_empty_authoritative_inventory(tmp_path: Path) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    empty_document = json.dumps({"schema_version": 2, "records": []})
    candidates.write_text(empty_document, encoding="utf-8")
    inventory.write_text(empty_document, encoding="utf-8")
    output = tmp_path / "observations.json"
    repository_root = Path(__file__).parents[2]

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.conformance.collector",
            "collect",
            "--candidates",
            str(candidates),
            "--inventory",
            str(inventory),
            "--output",
            str(output),
            "--root",
            str(tmp_path),
            "--runner-label",
            "test-runner",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "authoritative inventory is empty" in completed.stderr
    assert not output.exists()


# Q. Does collect_observation correctly pass staged probe basename to evaluation for filename records?
def test_collect_observation_passes_probe_name_for_filename_record(tmp_path: Path):
    fixture = tmp_path / "Gemfile"
    fixture.write_bytes(b'source "https://rubygems.org"\n')
    digest = sha256(fixture.read_bytes()).hexdigest()
    record = InventoryRecord(
        id="sample-gemfile",
        fixture=FixtureReference(path="Gemfile", sha256=digest),
        probe_extension=None,
        probe_filename="Gemfile",
        ground_truth=GroundTruth(
            mimes=("text/plain",),
            extensions=(),
            filenames=("Gemfile",),
        ),
        provenance="test fixture",
        ground_truth_review=GroundTruthReview(
            status="verified",
            reviewed_by="reviewer",
            reviewed_at="2026-08-28",
            evidence=("test evidence",),
            reason=None,
        ),
        backends=("magic",),
    )
    obs = collect_observation(
        record,
        backend="magic",
        root=tmp_path,
        runner_label="linux-x86_64",
    )
    assert obs["status"] == "ok"
    assert obs["evaluation"] is not None
    assert obs["evaluation"]["extension_match"] is True
    assert obs["evaluation"]["overall_match"] is True
