"""Tests for aggregating reviewed backend conformance observations."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path


def _reviewed_record(fixture: Path) -> dict[str, object]:
    return {
        "id": "sample",
        "fixture": fixture.name,
        "sha256": sha256(fixture.read_bytes()).hexdigest(),
        "probe_extension": ".txt",
        "ground_truth": {
            "mime_types": ["text/plain"],
            "extensions": [".txt"],
        },
        "provenance": "Synthetic reviewed fixture",
        "ground_truth_review": {
            "status": "verified",
            "reviewed_by": "test-reviewer",
            "reviewed_at": "2026-07-21",
            "evidence": ["https://example.test/sample"],
        },
        "backends": ["lexical", "magic", "magika", "hybrid"],
    }


def _write_reviewed_inventory(root: Path) -> tuple[Path, Path]:
    fixture = root / "sample.txt"
    fixture.write_bytes(b"reviewed conformance fixture")
    record = _reviewed_record(fixture)
    payload = {"schema_version": 1, "records": [record]}
    candidates = root / "candidates.json"
    inventory = root / "inventory.json"
    candidates.write_text(json.dumps(payload), encoding="utf-8")
    inventory.write_text(json.dumps(payload), encoding="utf-8")
    return candidates, inventory


def _observation(
    *,
    backend: str,
    runner_label: str,
    status: str = "ok",
) -> dict[str, object]:
    raw_output: dict[str, list[str]] | None = {
        "mime_types": ["text/plain"],
        "extensions": [".txt"],
    }
    semantic_output: dict[str, list[str]] | None = raw_output
    error: dict[str, str] | None = None
    if status == "no_result":
        raw_output = {"mime_types": [], "extensions": []}
        semantic_output = raw_output
    elif status == "error":
        raw_output = None
        semantic_output = None
        error = {"type": "RuntimeError", "message": "backend unavailable"}
    return {
        "inventory_id": "sample",
        "backend": backend,
        "platform": {
            "os": "TestOS",
            "architecture": "x86_64",
            "runner_label": runner_label,
        },
        "runtime": {
            "python": "3.12.0",
            "filetype_detector": "1.0.0",
            "python_magic": "0.4.27",
            "libmagic": "546",
            "libmagic_distribution": "test:libmagic=5.46",
            "magika": "0.6.1",
            "magika_model": "standard_v3_3",
        },
        "raw_output": raw_output,
        "semantic_output": semantic_output,
        "status": status,
        "error": error,
        "evaluation": {
            "mime_match": status == "ok",
            "extension_match": status == "ok",
            "overall_match": status == "ok",
        },
    }


def _complete_observations(runner_label: str) -> list[dict[str, object]]:
    return [
        _observation(backend=backend, runner_label=runner_label)
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]


def _write_artifact(path: Path, observations: list[dict[str, object]]) -> Path:
    inventory = path.parent / "inventory.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "inventory_sha256": sha256(inventory.read_bytes()).hexdigest(),
                "observations": observations,
            }
        ),
        encoding="utf-8",
    )
    return path


def _aggregate_command(
    *,
    candidates: Path,
    inventory: Path,
    root: Path,
    inputs: list[Path],
    output_dir: Path,
    baseline: Path | None = None,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "scripts.conformance.aggregate",
        "--candidates",
        str(candidates),
        "--inventory",
        str(inventory),
        "--root",
        str(root),
    ]
    for artifact in inputs:
        command.extend(["--input", str(artifact)])
    command.extend(
        [
            "--output-dir",
            str(output_dir),
            "--expected-runner-label",
            "ubuntu-test",
            "--expected-runner-label",
            "macos-test",
        ]
    )
    if baseline is not None:
        command.extend(["--baseline", str(baseline)])
    return command


# Q. Does a missing runner matrix reject before any report is produced?
def test_aggregate_command_rejects_incomplete_platform_matrix_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    artifact = _write_artifact(
        tmp_path / "ubuntu.json",
        [
            _observation(backend=backend, runner_label="ubuntu-test")
            for backend in ("lexical", "magic", "magika", "hybrid")
        ],
    )

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[artifact],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "missing runner artifacts: macos-test" in completed.stderr
    assert not output_dir.exists()


# Q. Do duplicate and unknown record/backend pairs reject before reports are written?
def test_aggregate_command_rejects_invalid_observation_matrix_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu_observations = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    ubuntu_observations.append(
        _observation(backend="lexical", runner_label="ubuntu-test")
    )
    artifacts = [
        _write_artifact(tmp_path / "ubuntu.json", ubuntu_observations),
        _write_artifact(
            tmp_path / "macos.json",
            [
                _observation(backend=backend, runner_label="macos-test")
                for backend in ("lexical", "magic", "magika", "hybrid")
            ],
        ),
    ]

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=artifacts,
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert (
        "duplicate observation for runner ubuntu-test: sample/lexical"
        in completed.stderr
    )
    assert not output_dir.exists()


# Q. Does a complete matrix render deterministic JSON, CSV, and evidence Markdown?
def test_aggregate_command_writes_deterministic_cross_platform_reports(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend="lexical", runner_label="ubuntu-test"),
        _observation(backend="magic", runner_label="ubuntu-test"),
        _observation(backend="magika", runner_label="ubuntu-test", status="no_result"),
        _observation(backend="hybrid", runner_label="ubuntu-test", status="error"),
    ]
    ubuntu[1]["raw_output"] = {
        "mime_types": ["application/x-other"],
        "extensions": [".other"],
    }
    ubuntu[1]["semantic_output"] = {
        "mime_types": ["application/x-other"],
        "extensions": [".other"],
    }
    ubuntu[1]["evaluation"] = {
        "mime_match": False,
        "extension_match": False,
        "overall_match": False,
    }
    macos = [
        _observation(backend="lexical", runner_label="macos-test"),
        _observation(backend="magic", runner_label="macos-test"),
        _observation(backend="magika", runner_label="macos-test", status="no_result"),
        _observation(backend="hybrid", runner_label="macos-test", status="error"),
    ]
    macos[0]["raw_output"] = {
        "mime_types": ["TEXT/PLAIN"],
        "extensions": ["txt"],
    }

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "macos.json", macos),
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    json_report = json.loads(
        (output_dir / "backend-conformance.json").read_text(encoding="utf-8")
    )
    assert [
        (row["platform"]["runner_label"], row["backend"])
        for row in json_report["observations"]
    ] == [
        ("ubuntu-test", "lexical"),
        ("ubuntu-test", "magic"),
        ("ubuntu-test", "magika"),
        ("ubuntu-test", "hybrid"),
        ("macos-test", "lexical"),
        ("macos-test", "magic"),
        ("macos-test", "magika"),
        ("macos-test", "hybrid"),
    ]
    with (output_dir / "backend-conformance.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        csv_rows = list(csv.DictReader(source))
    assert len(csv_rows) == 8
    assert csv_rows[0]["raw_output"] == (
        '{"extensions":[".txt"],"mime_types":["text/plain"]}'
    )
    assert csv_rows[1]["evaluation"] == (
        '{"extension_match":false,"mime_match":false,"overall_match":false}'
    )

    markdown = (output_dir / "backend-conformance.md").read_text(encoding="utf-8")
    for heading in (
        "## Inventory review",
        "## Execution matrix",
        "## Ground Truth correctness",
        "## Cross-platform divergence",
        "## Evidence rows",
    ):
        assert heading in markdown
    assert "libmagic distribution" in markdown
    assert "test:libmagic=5.46" in markdown
    assert "sample / magic" in markdown
    assert "sample / lexical" in markdown
    assert (
        'raw: {"first":{"extensions":[".other"],"mime_types":["application/x-other"]},'
        '"second":{"extensions":[".txt"],"mime_types":["text/plain"]}}'
    ) in markdown
    assert 'error: {"first":null,"second":null}' in markdown
    assert markdown.count("xychart-beta") == 2


# Q. Does inventory reporting retain unresolved and excluded candidates as non-facts?
def test_aggregate_reports_candidate_review_state_without_promoting_candidates(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    candidate_payload = json.loads(candidates.read_text(encoding="utf-8"))
    verified = candidate_payload["records"][0]
    needs_review = deepcopy(verified)
    needs_review["id"] = "needs-review"
    needs_review["probe_extension"] = ".aiff"
    needs_review["ground_truth"] = {
        "mime_types": ["application/x-pending"],
        "extensions": [".txt"],
    }
    needs_review["provenance"] = "Legacy suffix conflicts with independent review"
    needs_review["ground_truth_review"] = {
        "status": "needs_review",
        "reason": "Conflicting legacy declaration",
    }
    excluded = deepcopy(verified)
    excluded["id"] = "excluded"
    excluded["probe_extension"] = ".avif"
    excluded["ground_truth"] = {
        "mime_types": ["application/x-excluded"],
        "extensions": [".mp4"],
    }
    excluded["provenance"] = "Duplicate fixture intentionally excluded"
    excluded["ground_truth_review"] = {
        "status": "excluded",
        "reason": "Duplicate byte-identical fixture",
    }
    candidate_payload["records"].extend([needs_review, excluded])
    candidates.write_text(json.dumps(candidate_payload), encoding="utf-8")

    output_dir = tmp_path / "reports"
    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(
                    tmp_path / "ubuntu.json",
                    [
                        _observation(backend=backend, runner_label="ubuntu-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    markdown = (output_dir / "backend-conformance.md").read_text(encoding="utf-8")
    assert "| Candidate | 3 | 3 |" in markdown
    assert "| Verified | 1 | 1 |" in markdown
    assert "| Unresolved | 1 | 1 |" in markdown
    assert "| Excluded | 1 | 1 |" in markdown
    assert (
        "`needs-review`: Conflicting legacy declaration; "
        "provenance: Legacy suffix conflicts with independent review"
    ) in markdown
    report = json.loads(
        (output_dir / "backend-conformance.json").read_text(encoding="utf-8")
    )
    assert {row["inventory_id"] for row in report["observations"]} == {"sample"}


# Q. Does an artifact missing a required runtime field fail before report output?
def test_aggregate_command_rejects_invalid_observation_schema_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    runtime = ubuntu[0]["runtime"]
    assert isinstance(runtime, dict)
    runtime.pop("libmagic")

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "observation runtime libmagic must be present" in completed.stderr
    assert not output_dir.exists()


# Q. Does an artifact missing its selected libmagic distribution fail before output?
def test_aggregate_command_rejects_missing_libmagic_distribution_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    runtime = ubuntu[0]["runtime"]
    assert isinstance(runtime, dict)
    runtime.pop("libmagic_distribution")

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert (
        "observation runtime libmagic_distribution must be present" in completed.stderr
    )
    assert not output_dir.exists()


# Q. Does an empty output require no_result rather than an evaluated OK state?
def test_aggregate_command_rejects_empty_ok_observation_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    ubuntu[0]["raw_output"] = {"mime_types": [], "extensions": []}
    ubuntu[0]["semantic_output"] = {"mime_types": [], "extensions": []}
    ubuntu[0]["evaluation"] = {
        "mime_match": False,
        "extension_match": False,
        "overall_match": False,
    }

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "ok observations must contain at least one output value" in completed.stderr
    assert not output_dir.exists()


# Q. Does aggregate validation reject noncanonical semantic output tuples?
def test_aggregate_command_rejects_semantic_output_not_normalized_from_raw(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    ubuntu[0]["semantic_output"] = {
        "mime_types": ["TEXT/PLAIN"],
        "extensions": ["txt"],
    }

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "semantic_output must normalize raw_output" in completed.stderr
    assert not output_dir.exists()


# Q. Does an overall match require both component matches?
def test_aggregate_command_rejects_inconsistent_overall_match_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    ubuntu[0]["evaluation"] = {
        "mime_match": False,
        "extension_match": True,
        "overall_match": True,
    }

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "overall_match must equal mime_match and extension_match" in completed.stderr
    assert not output_dir.exists()


# Q. Does an artifact require an integer schema version rather than a boolean?
def test_aggregate_command_rejects_boolean_schema_version_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = _write_artifact(
        tmp_path / "ubuntu.json",
        [
            _observation(backend=backend, runner_label="ubuntu-test")
            for backend in ("lexical", "magic", "magika", "hybrid")
        ],
    )
    payload = json.loads(ubuntu.read_text(encoding="utf-8"))
    payload["schema_version"] = True
    ubuntu.write_text(json.dumps(payload), encoding="utf-8")

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                ubuntu,
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "must use integer schema_version 1" in completed.stderr
    assert not output_dir.exists()


# Q. Does an output tuple reject unknown fields instead of masking an empty result?
def test_aggregate_command_rejects_unknown_output_fields_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    ubuntu[0]["raw_output"] = {
        "mime_types": [],
        "extensions": [],
        "unexpected": ["not-an-output"],
    }
    ubuntu[0]["semantic_output"] = {"mime_types": [], "extensions": []}
    ubuntu[0]["evaluation"] = {
        "mime_match": False,
        "extension_match": False,
        "overall_match": False,
    }

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "observation raw_output has unknown fields: unexpected" in completed.stderr
    assert not output_dir.exists()


# Q. Does a collector row require nullable result fields to be present explicitly?
def test_aggregate_command_rejects_missing_nullable_result_field_before_writing(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    ubuntu = [
        _observation(backend=backend, runner_label="ubuntu-test")
        for backend in ("lexical", "magic", "magika", "hybrid")
    ]
    ubuntu[0].pop("error")

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(tmp_path / "ubuntu.json", ubuntu),
                _write_artifact(
                    tmp_path / "macos.json",
                    [
                        _observation(backend=backend, runner_label="macos-test")
                        for backend in ("lexical", "magic", "magika", "hybrid")
                    ],
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "observation error must be present" in completed.stderr
    assert not output_dir.exists()


# Q. Does a first matrix run emit a deterministic reviewable candidate baseline?
def test_aggregate_emits_candidate_baseline_when_no_baseline_exists(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    output_dir = tmp_path / "reports"
    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                _write_artifact(
                    tmp_path / "ubuntu.json",
                    _complete_observations("ubuntu-test"),
                ),
                _write_artifact(
                    tmp_path / "macos.json",
                    _complete_observations("macos-test"),
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    baseline = json.loads(
        (output_dir / "candidate-baseline.json").read_text(encoding="utf-8")
    )
    assert baseline["schema_version"] == 1
    assert len(baseline["observations"]) == 8
    assert baseline["observations"][0] == {
        "architecture": "x86_64",
        "backend": "lexical",
        "inventory_id": "sample",
        "probe_extension": ".txt",
        "runner_label": "ubuntu-test",
        "semantic_output": {
            "extensions": [".txt"],
            "mime_types": ["text/plain"],
        },
        "status": "ok",
    }
    report = json.loads(
        (output_dir / "backend-conformance.json").read_text(encoding="utf-8")
    )
    assert report["summary"]["baseline"] == {
        "change_count": 0,
        "changes": [],
        "status": "candidate",
    }
    markdown = (output_dir / "backend-conformance.md").read_text(encoding="utf-8")
    assert "## Baseline" in markdown
    assert "candidate-baseline.json" in markdown
    assert "## Inventory review" in markdown
    assert "| Unresolved |" in markdown
    assert "| Excluded |" in markdown
    assert "## Execution matrix" in markdown
    assert "libmagic distribution" in markdown
    assert "## Ground Truth correctness" in markdown
    assert "## Evidence rows" in markdown
    assert "## Reproduce" in markdown
    assert "python -m scripts.conformance.cli review" in markdown
    assert "python -m scripts.conformance.collector collect" in markdown
    assert "python -m scripts.conformance.aggregate" in markdown


# Q. Does an unchanged matrix match the reviewed baseline?
def test_aggregate_accepts_exact_semantic_baseline_match(tmp_path: Path) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    inputs = [
        _write_artifact(
            tmp_path / "ubuntu.json",
            _complete_observations("ubuntu-test"),
        ),
        _write_artifact(
            tmp_path / "macos.json",
            _complete_observations("macos-test"),
        ),
    ]
    initial_dir = tmp_path / "initial"
    initial = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=inputs,
            output_dir=initial_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )
    assert initial.returncode == 0, initial.stderr

    verified_dir = tmp_path / "verified"
    verified = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=inputs,
            output_dir=verified_dir,
            baseline=initial_dir / "candidate-baseline.json",
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert verified.returncode == 0, verified.stderr
    report = json.loads(
        (verified_dir / "backend-conformance.json").read_text(encoding="utf-8")
    )
    assert report["summary"]["baseline"] == {
        "change_count": 0,
        "changes": [],
        "status": "match",
    }
    assert not (verified_dir / "candidate-baseline.json").exists()


# Q. Does semantic drift write complete reports and fail with exit status 2?
def test_aggregate_fails_on_semantic_baseline_drift_after_writing_reports(
    tmp_path: Path,
) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    original_inputs = [
        _write_artifact(
            tmp_path / "ubuntu.json",
            _complete_observations("ubuntu-test"),
        ),
        _write_artifact(
            tmp_path / "macos.json",
            _complete_observations("macos-test"),
        ),
    ]
    initial_dir = tmp_path / "initial"
    initial = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=original_inputs,
            output_dir=initial_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )
    assert initial.returncode == 0, initial.stderr

    changed_macos = _complete_observations("macos-test")
    changed_macos[0]["raw_output"] = {
        "mime_types": ["text/plain"],
        "extensions": [".md"],
    }
    changed_macos[0]["semantic_output"] = {
        "mime_types": ["text/plain"],
        "extensions": [".md"],
    }
    changed_macos[0]["evaluation"] = {
        "mime_match": True,
        "extension_match": False,
        "overall_match": False,
    }
    changed_dir = tmp_path / "changed"
    changed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                original_inputs[0],
                _write_artifact(tmp_path / "macos-changed.json", changed_macos),
            ],
            output_dir=changed_dir,
            baseline=initial_dir / "candidate-baseline.json",
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert changed.returncode == 2, changed.stderr
    report = json.loads(
        (changed_dir / "backend-conformance.json").read_text(encoding="utf-8")
    )
    assert report["summary"]["baseline"]["status"] == "drift"
    assert report["summary"]["baseline"]["change_count"] == 1
    assert report["summary"]["baseline"]["changes"][0]["kind"] == "changed"
    assert (changed_dir / "backend-conformance.csv").is_file()
    assert (changed_dir / "backend-conformance.md").is_file()


# Q. Does raw-only ordering and spelling variation remain baseline-compatible?
def test_aggregate_ignores_raw_only_baseline_changes(tmp_path: Path) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    ubuntu = _complete_observations("ubuntu-test")
    macos = _complete_observations("macos-test")
    initial_inputs = [
        _write_artifact(tmp_path / "ubuntu.json", ubuntu),
        _write_artifact(tmp_path / "macos.json", macos),
    ]
    initial_dir = tmp_path / "initial"
    initial = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=initial_inputs,
            output_dir=initial_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )
    assert initial.returncode == 0, initial.stderr

    macos[0]["raw_output"] = {
        "mime_types": ["TEXT/PLAIN", "text/plain"],
        "extensions": ["TXT", ".txt"],
    }
    verified_dir = tmp_path / "verified"
    verified = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                initial_inputs[0],
                _write_artifact(tmp_path / "macos-raw-only.json", macos),
            ],
            output_dir=verified_dir,
            baseline=initial_dir / "candidate-baseline.json",
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert verified.returncode == 0, verified.stderr
    report = json.loads(
        (verified_dir / "backend-conformance.json").read_text(encoding="utf-8")
    )
    assert report["summary"]["baseline"]["status"] == "match"


# Q. Does aggregation reject observations collected from different reviewed facts?
def test_aggregate_rejects_stale_inventory_digest(tmp_path: Path) -> None:
    candidates, inventory = _write_reviewed_inventory(tmp_path)
    stale_path = _write_artifact(
        tmp_path / "stale.json",
        _complete_observations("ubuntu-test"),
    )
    stale_payload = json.loads(stale_path.read_text(encoding="utf-8"))
    stale_payload["inventory_sha256"] = "0" * 64
    stale_path.write_text(json.dumps(stale_payload), encoding="utf-8")
    output_dir = tmp_path / "reports"

    completed = subprocess.run(
        _aggregate_command(
            candidates=candidates,
            inventory=inventory,
            root=tmp_path,
            inputs=[
                stale_path,
                _write_artifact(
                    tmp_path / "macos.json",
                    _complete_observations("macos-test"),
                ),
            ],
            output_dir=output_dir,
        ),
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "inventory digest" in completed.stderr
    assert not output_dir.exists()
