"""Aggregate validated backend-conformance collector artifacts."""

from __future__ import annotations

import argparse
import hashlib
import csv
import itertools
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from scripts.conformance.evaluator import semantic_output as normalize_output
from scripts.conformance.inventory import (
    InventoryValidationError,
    load_verified_inventory,
    review_summary,
)
from scripts.conformance.types import InventoryRecord


class AggregateValidationError(ValueError):
    """Raised when collector artifacts cannot support a complete report."""


_BACKENDS = ("lexical", "magic", "magika", "hybrid")
_OBSERVATION_STATUSES = frozenset({"ok", "no_result", "error"})
_RUNTIME_FIELDS = (
    "python",
    "filetype_detector",
    "python_magic",
    "libmagic",
    "libmagic_distribution",
    "magika",
    "magika_model",
)
_EVALUATION_FIELDS = ("mime_match", "extension_match", "overall_match")
_BASELINE_KEY_FIELDS = (
    "runner_label",
    "architecture",
    "inventory_id",
    "probe_extension",
    "backend",
)
_BASELINE_OBSERVATION_FIELDS = frozenset(
    (*_BASELINE_KEY_FIELDS, "status", "semantic_output")
)


def aggregate_artifacts(
    *,
    candidates_path: Path,
    inventory_path: Path,
    root: Path,
    input_paths: Sequence[Path],
    expected_runner_labels: Sequence[str],
    baseline_path: Path | None = None,
) -> dict[str, object]:
    """Validate and order collector artifacts before rendering reports."""
    records = load_verified_inventory(candidates_path, inventory_path, root=root)
    if not records:
        raise AggregateValidationError("authoritative inventory is empty")

    expected_labels = _expected_runner_labels(expected_runner_labels)
    expected_pairs = tuple(
        (record.id, backend) for record in records for backend in record.backends
    )
    expected_pair_set = set(expected_pairs)
    artifacts = [_load_artifact(path) for path in input_paths]
    inventory_sha256 = _file_digest(inventory_path)
    for path, artifact in zip(input_paths, artifacts, strict=True):
        artifact_digest = _require_text(
            artifact.get("inventory_sha256"), f"artifact {path} inventory digest"
        )
        if artifact_digest != inventory_sha256:
            raise AggregateValidationError(
                f"artifact {path} inventory digest does not match "
                "the authoritative inventory"
            )
    artifact_labels = [_artifact_runner_label(artifact) for artifact in artifacts]
    _validate_runner_artifacts(
        artifact_labels,
        expected_runner_labels=expected_labels,
    )

    observations_by_runner: dict[str, dict[tuple[str, str], dict[str, object]]] = {}
    for artifact, runner_label in zip(artifacts, artifact_labels, strict=True):
        observations_by_runner[runner_label] = _validate_observation_matrix(
            artifact,
            runner_label=runner_label,
            expected_pairs=expected_pairs,
            expected_pair_set=expected_pair_set,
        )

    observations = [
        observations_by_runner[runner_label][pair]
        for runner_label in expected_labels
        for pair in expected_pairs
    ]
    summary = _build_summary(
        observations_by_runner=observations_by_runner,
        records=records,
        runner_labels=expected_labels,
        candidates_path=candidates_path,
        inventory_path=inventory_path,
        root=root,
    )
    candidate_baseline = _build_candidate_baseline(
        observations,
        records=records,
        inventory_sha256=inventory_sha256,
    )
    summary["baseline"] = _compare_baseline(
        candidate_baseline,
        baseline_path=baseline_path,
    )
    return {
        "schema_version": 1,
        "observations": observations,
        "summary": summary,
        "_candidate_baseline": candidate_baseline,
    }


def _build_candidate_baseline(
    observations: Sequence[Mapping[str, object]],
    *,
    records: Sequence[InventoryRecord],
    inventory_sha256: str,
) -> dict[str, object]:
    records_by_id = {record.id: record for record in records}
    rows: list[dict[str, object]] = []
    for observation in observations:
        inventory_id = _require_text(
            observation.get("inventory_id"), "baseline inventory_id"
        )
        record = records_by_id[inventory_id]
        platform = _mapping(observation["platform"])
        semantic_output = observation["semantic_output"]
        rows.append(
            {
                "runner_label": _require_text(
                    platform.get("runner_label"), "baseline runner_label"
                ),
                "architecture": _require_text(
                    platform.get("architecture"), "baseline architecture"
                ),
                "inventory_id": inventory_id,
                "probe_extension": record.probe_extension,
                "backend": _require_text(
                    observation.get("backend"), "baseline backend"
                ),
                "status": _require_text(observation.get("status"), "baseline status"),
                "semantic_output": semantic_output,
            }
        )
    return {
        "schema_version": 1,
        "inventory_sha256": inventory_sha256,
        "observations": rows,
    }


def _compare_baseline(
    candidate: Mapping[str, object],
    *,
    baseline_path: Path | None,
) -> dict[str, object]:
    if baseline_path is None:
        return {"status": "candidate", "change_count": 0, "changes": []}

    baseline_payload = _load_artifact(baseline_path)
    baseline_rows = _baseline_rows(baseline_payload)
    candidate_rows = _baseline_rows(candidate)
    baseline_by_key = {_baseline_key(row): row for row in baseline_rows}
    candidate_by_key = {_baseline_key(row): row for row in candidate_rows}
    baseline_digest = _require_text(
        baseline_payload.get("inventory_sha256"), "baseline inventory digest"
    )
    candidate_digest = _require_text(
        candidate.get("inventory_sha256"), "candidate inventory digest"
    )
    changes: list[dict[str, object]] = []
    if baseline_digest != candidate_digest:
        changes.append(
            {
                "kind": "inventory_changed",
                "key": None,
                "baseline": baseline_digest,
                "current": candidate_digest,
            }
        )
    for key in sorted(set(baseline_by_key) | set(candidate_by_key)):
        baseline_row = baseline_by_key.get(key)
        candidate_row = candidate_by_key.get(key)
        if baseline_row is None:
            kind = "new"
        elif candidate_row is None:
            kind = "missing"
        elif baseline_row == candidate_row:
            continue
        else:
            kind = "changed"
        changes.append(
            {
                "kind": kind,
                "key": dict(zip(_BASELINE_KEY_FIELDS, key, strict=True)),
                "baseline": baseline_row,
                "current": candidate_row,
            }
        )
    return {
        "status": "drift" if changes else "match",
        "change_count": len(changes),
        "changes": changes,
    }


def _baseline_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_rows = payload["observations"]
    assert isinstance(raw_rows, list)
    rows: list[Mapping[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            raise AggregateValidationError("baseline observation must be an object")
        fields = frozenset(raw_row)
        if fields != _BASELINE_OBSERVATION_FIELDS:
            missing = sorted(_BASELINE_OBSERVATION_FIELDS - fields)
            unknown = sorted(fields - _BASELINE_OBSERVATION_FIELDS)
            raise AggregateValidationError(
                "baseline observation fields must match the schema; "
                f"missing={missing}, unknown={unknown}"
            )
        status = _require_text(raw_row.get("status"), "baseline status")
        if status not in _OBSERVATION_STATUSES:
            raise AggregateValidationError(
                f"baseline status must be one of {sorted(_OBSERVATION_STATUSES)}"
            )
        semantic_output = raw_row.get("semantic_output")
        if semantic_output is None:
            if status != "error":
                raise AggregateValidationError(
                    "baseline semantic_output may be null only for error status"
                )
        else:
            _validate_output(semantic_output, field="baseline semantic_output")
        key = _baseline_key(raw_row)
        if key in seen:
            raise AggregateValidationError(f"duplicate baseline observation key: {key}")
        seen.add(key)
        rows.append(raw_row)
    return rows


def _baseline_key(row: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(
        _require_text(row.get(field), f"baseline {field}")
        for field in _BASELINE_KEY_FIELDS
    )


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_runner_labels(labels: Sequence[str]) -> tuple[str, ...]:
    if not labels or any(not label.strip() for label in labels):
        raise AggregateValidationError("expected runner labels must be non-empty")
    if len(set(labels)) != len(labels):
        raise AggregateValidationError("expected runner labels must be unique")
    return tuple(labels)


def _load_artifact(path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AggregateValidationError(
            f"cannot read artifact {path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise AggregateValidationError(
            f"artifact {path} must use integer schema_version 1"
        )
    schema_version = payload.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        raise AggregateValidationError(
            f"artifact {path} must use integer schema_version 1"
        )
    observations = payload.get("observations")
    if not isinstance(observations, list) or not observations:
        raise AggregateValidationError(f"artifact {path} must contain observations")
    return payload


def _artifact_runner_label(artifact: Mapping[str, object]) -> str:
    observations = artifact["observations"]
    assert isinstance(observations, list)
    labels: set[str] = set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise AggregateValidationError("artifact observations must be objects")
        platform = observation.get("platform")
        if not isinstance(platform, dict):
            raise AggregateValidationError("observation platform must be an object")
        label = platform.get("runner_label")
        if not isinstance(label, str) or not label.strip():
            raise AggregateValidationError("observation runner_label must be non-empty")
        labels.add(label)
    if len(labels) != 1:
        raise AggregateValidationError("artifact mixes runner labels")
    return next(iter(labels))


def _validate_runner_artifacts(
    artifact_labels: Sequence[str],
    *,
    expected_runner_labels: Sequence[str],
) -> None:
    duplicate_labels = sorted(
        {label for label in artifact_labels if artifact_labels.count(label) > 1}
    )
    if duplicate_labels:
        raise AggregateValidationError(
            "duplicate runner artifacts: " + ", ".join(duplicate_labels)
        )

    unexpected = sorted(set(artifact_labels).difference(expected_runner_labels))
    if unexpected:
        raise AggregateValidationError(
            "unexpected runner artifacts: " + ", ".join(unexpected)
        )
    missing = [
        label for label in expected_runner_labels if label not in artifact_labels
    ]
    if missing:
        raise AggregateValidationError(
            "missing runner artifacts: " + ", ".join(missing)
        )


def _validate_observation_matrix(
    artifact: Mapping[str, object],
    *,
    runner_label: str,
    expected_pairs: Sequence[tuple[str, str]],
    expected_pair_set: set[tuple[str, str]],
) -> dict[tuple[str, str], dict[str, object]]:
    observations = artifact["observations"]
    assert isinstance(observations, list)
    observations_by_pair: dict[tuple[str, str], dict[str, object]] = {}
    for raw_observation in observations:
        observation = _validate_observation(raw_observation, runner_label=runner_label)
        pair = (observation["inventory_id"], observation["backend"])
        assert isinstance(pair[0], str)
        assert isinstance(pair[1], str)
        if pair not in expected_pair_set:
            raise AggregateValidationError(
                f"unknown observation for runner {runner_label}: {pair[0]}/{pair[1]}"
            )
        if pair in observations_by_pair:
            raise AggregateValidationError(
                f"duplicate observation for runner {runner_label}: {pair[0]}/{pair[1]}"
            )
        observations_by_pair[pair] = observation

    missing_pairs = [
        pair for pair in expected_pairs if pair not in observations_by_pair
    ]
    if missing_pairs:
        missing = ", ".join(
            f"{inventory_id}/{backend}" for inventory_id, backend in missing_pairs
        )
        raise AggregateValidationError(
            f"missing observations for runner {runner_label}: {missing}"
        )
    return observations_by_pair


def _validate_observation(
    raw_observation: object,
    *,
    runner_label: str,
) -> dict[str, object]:
    if not isinstance(raw_observation, dict):
        raise AggregateValidationError("artifact observations must be objects")
    observation = dict(raw_observation)
    _require_text(observation.get("inventory_id"), "observation inventory_id")
    _require_text(observation.get("backend"), "observation backend")
    _validate_platform(observation.get("platform"), runner_label=runner_label)
    _validate_runtime(observation.get("runtime"))
    _validate_result_fields(observation)
    return observation


def _validate_platform(value: object, *, runner_label: str) -> None:
    if not isinstance(value, dict):
        raise AggregateValidationError("observation platform must be an object")
    _require_text(value.get("os"), "observation platform os")
    _require_text(value.get("architecture"), "observation platform architecture")
    actual_label = _require_text(
        value.get("runner_label"),
        "observation platform runner_label",
    )
    if actual_label != runner_label:
        raise AggregateValidationError("artifact mixes runner labels")


def _validate_runtime(value: object) -> None:
    if not isinstance(value, dict):
        raise AggregateValidationError("observation runtime must be an object")
    for field in _RUNTIME_FIELDS:
        if field not in value:
            raise AggregateValidationError(
                f"observation runtime {field} must be present"
            )
        runtime_value = value[field]
        if runtime_value is not None and not isinstance(runtime_value, str):
            raise AggregateValidationError(
                f"observation runtime {field} must be text or null"
            )


def _validate_result_fields(observation: Mapping[str, object]) -> None:
    required_fields = ("status", "raw_output", "semantic_output", "error", "evaluation")
    missing_fields = sorted(
        field for field in required_fields if field not in observation
    )
    if missing_fields:
        raise AggregateValidationError(
            f"observation {', '.join(missing_fields)} must be present"
        )
    status = observation.get("status")
    if status not in _OBSERVATION_STATUSES:
        raise AggregateValidationError(
            "observation status must be ok, no_result, or error"
        )
    raw_output = observation.get("raw_output")
    semantic_output = observation.get("semantic_output")
    error = observation.get("error")
    evaluation = observation.get("evaluation")

    if status == "error":
        if raw_output is not None or semantic_output is not None:
            raise AggregateValidationError(
                "error observations must not have output tuples"
            )
        _validate_error(error)
    else:
        _validate_output(raw_output, field="raw_output")
        _validate_output(semantic_output, field="semantic_output")
        if error is not None:
            raise AggregateValidationError(
                "successful observations must not have an error"
            )
        assert isinstance(raw_output, dict)
        assert isinstance(semantic_output, dict)
        raw_mimes = raw_output["mime_types"]
        raw_extensions = raw_output["extensions"]
        assert isinstance(raw_mimes, list)
        assert isinstance(raw_extensions, list)
        if semantic_output != normalize_output(
            mime_types=raw_mimes,
            extensions=raw_extensions,
        ):
            raise AggregateValidationError("semantic_output must normalize raw_output")
        if status == "no_result":
            if raw_mimes or raw_extensions:
                raise AggregateValidationError(
                    "no_result observations must have empty outputs"
                )
        elif not raw_mimes and not raw_extensions:
            raise AggregateValidationError(
                "ok observations must contain at least one output value"
            )
    _validate_evaluation(evaluation, status=status)


def _validate_output(value: object, *, field: str) -> None:
    if not isinstance(value, dict):
        raise AggregateValidationError(f"observation {field} must be an object")
    unknown_fields = sorted(set(value).difference({"mime_types", "extensions"}))
    if unknown_fields:
        raise AggregateValidationError(
            f"observation {field} has unknown fields: {', '.join(unknown_fields)}"
        )
    for tuple_field in ("mime_types", "extensions"):
        tuple_value = value.get(tuple_field)
        if not isinstance(tuple_value, list) or any(
            not isinstance(item, str) for item in tuple_value
        ):
            raise AggregateValidationError(
                f"observation {field} {tuple_field} must be a list of text"
            )


def _validate_error(value: object) -> None:
    if not isinstance(value, dict):
        raise AggregateValidationError(
            "error observations must include an error object"
        )
    _require_text(value.get("type"), "observation error type")
    _require_text(value.get("message"), "observation error message")


def _validate_evaluation(value: object, *, status: object) -> None:
    if not isinstance(value, dict):
        raise AggregateValidationError("observation evaluation must be an object")
    for field in _EVALUATION_FIELDS:
        if not isinstance(value.get(field), bool):
            raise AggregateValidationError(
                f"observation evaluation {field} must be boolean"
            )
    mime_match = value["mime_match"]
    extension_match = value["extension_match"]
    overall_match = value["overall_match"]
    assert isinstance(mime_match, bool)
    assert isinstance(extension_match, bool)
    assert isinstance(overall_match, bool)
    if overall_match != (mime_match and extension_match):
        raise AggregateValidationError(
            "overall_match must equal mime_match and extension_match"
        )
    if status != "ok" and any(value[field] for field in _EVALUATION_FIELDS):
        raise AggregateValidationError(
            "no_result and error observations must not report a Ground Truth match"
        )


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AggregateValidationError(f"{field} must be non-empty text")
    return value


def _build_summary(
    *,
    observations_by_runner: Mapping[str, Mapping[tuple[str, str], dict[str, object]]],
    records: Sequence[InventoryRecord],
    runner_labels: Sequence[str],
    candidates_path: Path,
    inventory_path: Path,
    root: Path,
) -> dict[str, object]:
    return {
        "inventory_review": review_summary(
            candidates_path,
            inventory_path,
            root=root,
        ),
        "execution_matrix": _execution_matrix(
            observations_by_runner,
            runner_labels=runner_labels,
            records=records,
        ),
        "ground_truth_correctness": _ground_truth_correctness(
            observations_by_runner,
            runner_labels=runner_labels,
            records=records,
        ),
        "cross_platform_divergence": _cross_platform_divergence(
            observations_by_runner,
            runner_labels=runner_labels,
            records=records,
        ),
    }


def _execution_matrix(
    observations_by_runner: Mapping[str, Mapping[tuple[str, str], dict[str, object]]],
    *,
    runner_labels: Sequence[str],
    records: Sequence[InventoryRecord],
) -> list[dict[str, object]]:
    first_pair = (records[0].id, records[0].backends[0])
    rows: list[dict[str, object]] = []
    for runner_label in runner_labels:
        observation = observations_by_runner[runner_label][first_pair]
        platform = _mapping(observation["platform"])
        runtime = _mapping(observation["runtime"])
        rows.append(
            {
                "runner_label": runner_label,
                "os": platform["os"],
                "architecture": platform["architecture"],
                **{field: runtime[field] for field in _RUNTIME_FIELDS},
            }
        )
    return rows


def _ground_truth_correctness(
    observations_by_runner: Mapping[str, Mapping[tuple[str, str], dict[str, object]]],
    *,
    runner_labels: Sequence[str],
    records: Sequence[InventoryRecord],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for runner_label in runner_labels:
        for backend in _backend_order(records):
            observations = [
                observations_by_runner[runner_label][(record.id, backend)]
                for record in records
                if backend in record.backends
            ]
            total = len(observations)
            counts = {
                "evaluated": sum(item["status"] == "ok" for item in observations),
                "correct": sum(_is_correct(item) for item in observations),
                "incorrect": sum(
                    item["status"] == "ok" and not _is_correct(item)
                    for item in observations
                ),
                "no_result": sum(
                    item["status"] == "no_result" for item in observations
                ),
                "error": sum(item["status"] == "error" for item in observations),
            }
            rows.append(
                {
                    "runner_label": runner_label,
                    "backend": backend,
                    "total": total,
                    **{f"{name}_count": count for name, count in counts.items()},
                    **{
                        f"{name}_rate": _rate(count, total)
                        for name, count in counts.items()
                    },
                }
            )
    return rows


def _cross_platform_divergence(
    observations_by_runner: Mapping[str, Mapping[tuple[str, str], dict[str, object]]],
    *,
    runner_labels: Sequence[str],
    records: Sequence[InventoryRecord],
) -> dict[str, object]:
    pair_summaries: list[dict[str, object]] = []
    semantic_rows: list[dict[str, object]] = []
    raw_only_rows: list[dict[str, object]] = []
    for runner_a, runner_b in itertools.combinations(runner_labels, 2):
        for backend in _backend_order(records):
            pairs = [
                (record.id, backend) for record in records if backend in record.backends
            ]
            semantic_count = 0
            raw_only_count = 0
            for pair in pairs:
                observation_a = observations_by_runner[runner_a][pair]
                observation_b = observations_by_runner[runner_b][pair]
                row: dict[str, object] = {
                    "runner_a": runner_a,
                    "runner_b": runner_b,
                    "inventory_id": pair[0],
                    "backend": backend,
                    "observation_a": observation_a,
                    "observation_b": observation_b,
                }
                if _semantic_divergence(observation_a, observation_b):
                    semantic_count += 1
                    semantic_rows.append(row)
                elif _raw_only_difference(observation_a, observation_b):
                    raw_only_count += 1
                    raw_only_rows.append(row)
            pair_summaries.append(
                {
                    "runner_a": runner_a,
                    "runner_b": runner_b,
                    "backend": backend,
                    "total": len(pairs),
                    "semantic_divergence_count": semantic_count,
                    "semantic_divergence_rate": _rate(semantic_count, len(pairs)),
                    "raw_only_difference_count": raw_only_count,
                    "raw_only_difference_rate": _rate(raw_only_count, len(pairs)),
                }
            )
    return {
        "by_runner_pair": pair_summaries,
        "semantic_divergences": semantic_rows,
        "raw_only_differences": raw_only_rows,
    }


def _backend_order(records: Sequence[InventoryRecord]) -> tuple[str, ...]:
    return tuple(
        backend
        for backend in _BACKENDS
        if any(backend in record.backends for record in records)
    )


def _is_correct(observation: Mapping[str, object]) -> bool:
    evaluation = _mapping(observation["evaluation"])
    return observation["status"] == "ok" and evaluation["overall_match"] is True


def _semantic_divergence(
    observation_a: Mapping[str, object],
    observation_b: Mapping[str, object],
) -> bool:
    return (
        observation_a["status"] != observation_b["status"]
        or observation_a["semantic_output"] != observation_b["semantic_output"]
    )


def _raw_only_difference(
    observation_a: Mapping[str, object],
    observation_b: Mapping[str, object],
) -> bool:
    return (
        observation_a["status"] == observation_b["status"]
        and observation_a["semantic_output"] == observation_b["semantic_output"]
        and observation_a["raw_output"] != observation_b["raw_output"]
    )


def _rate(count: int, total: int) -> float:
    return round(100 * count / total, 2) if total else 0.0


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, dict)
    return value


def write_reports(
    result: Mapping[str, object],
    *,
    output_dir: Path,
    records: Sequence[InventoryRecord],
) -> None:
    """Write deterministic evidence reports and a first-run candidate baseline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    public_result = dict(result)
    candidate_baseline = public_result.pop("_candidate_baseline")
    (output_dir / "backend-conformance.json").write_text(
        json.dumps(public_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    observations = public_result["observations"]
    assert isinstance(observations, list)
    _write_csv(output_dir / "backend-conformance.csv", observations)
    (output_dir / "backend-conformance.md").write_text(
        render_markdown(public_result, records=records),
        encoding="utf-8",
    )
    summary = _mapping(public_result["summary"])
    baseline = _mapping(summary["baseline"])
    if baseline["status"] == "candidate":
        (output_dir / "candidate-baseline.json").write_text(
            json.dumps(candidate_baseline, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _write_csv(path: Path, observations: Sequence[object]) -> None:
    fieldnames = (
        "runner_label",
        "inventory_id",
        "backend",
        "status",
        "os",
        "architecture",
        *_RUNTIME_FIELDS,
        "raw_output",
        "semantic_output",
        "error",
        "evaluation",
    )
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        for raw_observation in observations:
            assert isinstance(raw_observation, dict)
            platform = _mapping(raw_observation["platform"])
            runtime = _mapping(raw_observation["runtime"])
            writer.writerow(
                {
                    "runner_label": platform["runner_label"],
                    "inventory_id": raw_observation["inventory_id"],
                    "backend": raw_observation["backend"],
                    "status": raw_observation["status"],
                    "os": platform["os"],
                    "architecture": platform["architecture"],
                    **{field: runtime[field] for field in _RUNTIME_FIELDS},
                    "raw_output": _json(raw_observation["raw_output"]),
                    "semantic_output": _json(raw_observation["semantic_output"]),
                    "error": _json(raw_observation["error"]),
                    "evaluation": _json(raw_observation["evaluation"]),
                }
            )


def render_markdown(
    result: Mapping[str, object],
    *,
    records: Sequence[InventoryRecord],
) -> str:
    """Render the review, execution, correctness, divergence, and baseline sections."""
    summary = _mapping(result["summary"])
    inventory_review = _mapping(summary["inventory_review"])
    execution_matrix = _list_of_mappings(summary["execution_matrix"])
    correctness = _list_of_mappings(summary["ground_truth_correctness"])
    divergence = _mapping(summary["cross_platform_divergence"])
    baseline = _mapping(summary["baseline"])
    semantic_rows = _list_of_mappings(divergence["semantic_divergences"])
    raw_only_rows = _list_of_mappings(divergence["raw_only_differences"])
    pair_summaries = _list_of_mappings(divergence["by_runner_pair"])
    records_by_id = {record.id: record for record in records}

    lines = ["# Backend conformance", "", "## Inventory review", ""]
    lines.extend(_render_inventory_review(inventory_review))
    lines.extend(["", "## Execution matrix", ""])
    lines.extend(_render_execution_matrix(execution_matrix))
    lines.extend(["", "## Ground Truth correctness", ""])
    lines.extend(_render_correctness(correctness))
    lines.extend(_render_mismatch_chart(correctness))
    lines.extend(["", "## Cross-platform divergence", ""])
    lines.extend(_render_divergence(pair_summaries, semantic_rows, raw_only_rows))
    lines.extend(_render_divergence_chart(semantic_rows, records))
    lines.extend(["", "## Baseline", ""])
    lines.extend(_render_baseline(baseline))
    lines.extend(["", "## Evidence rows", ""])
    lines.extend(
        _render_evidence_rows(
            observations=_list_of_mappings(result["observations"]),
            semantic_rows=semantic_rows,
            records_by_id=records_by_id,
        )
    )
    return "\n".join(lines) + "\n"


def _render_baseline(baseline: Mapping[str, object]) -> list[str]:
    status = baseline["status"]
    if status == "candidate":
        return [
            "No reviewed baseline was supplied. "
            "`candidate-baseline.json` was generated for review."
        ]
    if status == "match":
        return ["The reviewed baseline matches every semantic observation."]
    changes = _list_of_mappings(baseline["changes"])
    lines = [f"Semantic baseline drift: {len(changes)} change(s).", ""]
    lines.extend(f"- {_json(change)}" for change in changes)
    return lines


def _render_inventory_review(review: Mapping[str, object]) -> list[str]:
    counts = (
        ("Candidate", "candidate_count", "candidate_suffix_count"),
        ("Verified", "verified_count", "verified_suffix_count"),
        ("Unresolved", "unresolved_count", "unresolved_suffix_count"),
        ("Excluded", "excluded_count", "excluded_suffix_count"),
    )
    lines = ["| Review state | Records | Unique suffixes |", "| --- | ---: | ---: |"]
    lines.extend(
        f"| {label} | {review.get(record_count, 0)} | {review.get(suffix_count, 0)} |"
        for label, record_count, suffix_count in counts
    )
    unresolved = review.get("unresolved", [])
    assert isinstance(unresolved, list)
    if unresolved:
        lines.extend(["", "### Unresolved candidates"])
        for raw_candidate in unresolved:
            candidate = _mapping(raw_candidate)
            lines.append(
                "- "
                f"`{candidate['id']}`: {candidate.get('reason') or 'no reason supplied'}; "
                f"provenance: {candidate.get('provenance') or 'not supplied'}; "
                f"MIME: {_json(candidate.get('mimes', []))}; "
                f"extensions: {_json(candidate.get('extensions', []))}"
            )
    else:
        lines.extend(["", "No unresolved candidates."])
    return lines


def _render_execution_matrix(rows: Sequence[Mapping[str, object]]) -> list[str]:
    headings = (
        "Runner label",
        "OS",
        "Architecture",
        "Python",
        "filetype-detector",
        "libmagic",
        "libmagic distribution",
        "Magika package",
        "Magika model",
    )
    fields = (
        "runner_label",
        "os",
        "architecture",
        "python",
        "filetype_detector",
        "libmagic",
        "libmagic_distribution",
        "magika",
        "magika_model",
    )
    lines = [
        "| " + " | ".join(headings) + " |",
        "| " + " | ".join("---" for _ in headings) + " |",
    ]
    lines.extend(
        "| " + " | ".join(_display(row[field]) for field in fields) + " |"
        for row in rows
    )
    return lines


def _render_correctness(rows: Sequence[Mapping[str, object]]) -> list[str]:
    headings = (
        "Runner",
        "Backend",
        "Evaluated",
        "Correct",
        "Incorrect",
        "No-result",
        "Error",
    )
    lines = [
        "Rates use all observations for the runner/backend.",
        "",
        "| " + " | ".join(headings) + " |",
        "| " + " | ".join("---" for _ in headings) + " |",
    ]
    for row in rows:
        cells = [row["runner_label"], row["backend"]]
        for name in ("evaluated", "correct", "incorrect", "no_result", "error"):
            cells.append(f"{row[f'{name}_count']} ({row[f'{name}_rate']}%)")
        lines.append("| " + " | ".join(_display(cell) for cell in cells) + " |")
    return lines


def _render_mismatch_chart(rows: Sequence[Mapping[str, object]]) -> list[str]:
    labels = [f"{row['runner_label']}/{row['backend']}" for row in rows]
    counts: list[int] = []
    for row in rows:
        count = row["incorrect_count"]
        assert isinstance(count, int)
        counts.append(count)
    return [
        "",
        *_xychart("Ground Truth mismatches by backend and runner", labels, counts),
    ]


def _render_divergence(
    summaries: Sequence[Mapping[str, object]],
    semantic_rows: Sequence[Mapping[str, object]],
    raw_only_rows: Sequence[Mapping[str, object]],
) -> list[str]:
    lines = [
        "| Runner pair | Backend | Semantic divergence | Raw-only difference |",
        "| --- | --- | ---: | ---: |",
    ]
    lines.extend(
        "| "
        f"{row['runner_a']} ↔ {row['runner_b']} | {row['backend']} | "
        f"{row['semantic_divergence_count']} ({row['semantic_divergence_rate']}%) | "
        f"{row['raw_only_difference_count']} ({row['raw_only_difference_rate']}%) |"
        for row in summaries
    )
    if semantic_rows or raw_only_rows:
        lines.extend(["", "### Identified rows"])
        lines.extend(
            "- Semantic divergence: "
            f"{row['inventory_id']} / {row['backend']} "
            f"({row['runner_a']} ↔ {row['runner_b']})"
            for row in semantic_rows
        )
        lines.extend(
            "- Raw-only difference: "
            f"{row['inventory_id']} / {row['backend']} "
            f"({row['runner_a']} ↔ {row['runner_b']})"
            for row in raw_only_rows
        )
    else:
        lines.extend(["", "No cross-platform divergences."])
    return lines


def _render_divergence_chart(
    semantic_rows: Sequence[Mapping[str, object]],
    records: Sequence[InventoryRecord],
) -> list[str]:
    backends = _backend_order(records)
    counts = [
        sum(row["backend"] == backend for row in semantic_rows) for backend in backends
    ]
    return ["", *_xychart("Semantic divergences by backend", list(backends), counts)]


def _xychart(title: str, labels: Sequence[str], counts: Sequence[int]) -> list[str]:
    ceiling = max(max(counts, default=0), 1)
    return [
        "```mermaid",
        "xychart-beta",
        f'    title "{title}"',
        f"    x-axis {json.dumps(list(labels))}",
        f'    y-axis "Count" 0 --> {ceiling}',
        "    bar " + json.dumps(list(counts)),
        "```",
    ]


def _render_evidence_rows(
    *,
    observations: Sequence[Mapping[str, object]],
    semantic_rows: Sequence[Mapping[str, object]],
    records_by_id: Mapping[str, InventoryRecord],
) -> list[str]:
    lines: list[str] = []
    for row in semantic_rows:
        record = records_by_id[str(row["inventory_id"])]
        lines.append(
            _evidence_line(
                category="Semantic divergence",
                record=record,
                backend=str(row["backend"]),
                runner=f"{row['runner_a']} ↔ {row['runner_b']}",
                raw_output={
                    "first": _mapping(row["observation_a"])["raw_output"],
                    "second": _mapping(row["observation_b"])["raw_output"],
                },
                semantic_output={
                    "first": _mapping(row["observation_a"])["semantic_output"],
                    "second": _mapping(row["observation_b"])["semantic_output"],
                },
                error={
                    "first": _mapping(row["observation_a"])["error"],
                    "second": _mapping(row["observation_b"])["error"],
                },
            )
        )
    for observation in observations:
        record = records_by_id[str(observation["inventory_id"])]
        status = observation["status"]
        if _is_correct(observation):
            continue
        category = "Ground Truth mismatch"
        if status == "no_result":
            category = "No-result"
        elif status == "error":
            category = "Error"
        platform = _mapping(observation["platform"])
        lines.append(
            _evidence_line(
                category=category,
                record=record,
                backend=str(observation["backend"]),
                runner=str(platform["runner_label"]),
                raw_output=observation["raw_output"],
                semantic_output=observation["semantic_output"],
                error=observation["error"],
            )
        )
    return lines or [
        "No mismatch, no-result, error, or semantic divergence evidence rows."
    ]


def _evidence_line(
    *,
    category: str,
    record: InventoryRecord,
    backend: str,
    runner: str,
    raw_output: object,
    semantic_output: object,
    error: object,
) -> str:
    expected = {
        "mime_types": list(record.ground_truth.mimes),
        "extensions": list(record.ground_truth.extensions),
    }
    return (
        f"- {category}: {record.id} / {backend} ({runner}); "
        f"expected: {_json(expected)}; raw: {_json(raw_output)}; "
        f"semantic: {_json(semantic_output)}; error: {_json(error)}"
    )


def _list_of_mappings(value: object) -> list[Mapping[str, object]]:
    assert isinstance(value, list)
    return [_mapping(item) for item in value]


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _display(value: object) -> str:
    return "unavailable" if value is None else str(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--expected-runner-label",
        action="append",
        dest="expected_runner_labels",
        required=True,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Aggregate complete collector matrices into evidence reports."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result = aggregate_artifacts(
            candidates_path=args.candidates,
            inventory_path=args.inventory,
            root=args.root,
            input_paths=args.input,
            expected_runner_labels=args.expected_runner_labels,
            baseline_path=args.baseline,
        )
        records = load_verified_inventory(
            args.candidates,
            args.inventory,
            root=args.root,
        )
        write_reports(result, output_dir=args.output_dir, records=records)
    except (AggregateValidationError, InventoryValidationError) as error:
        parser.error(str(error))
    summary = _mapping(result["summary"])
    baseline = _mapping(summary["baseline"])
    return 2 if baseline["status"] == "drift" else 0


if __name__ == "__main__":
    raise SystemExit(main())
