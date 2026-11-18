"""Compare complete, checkout-bound Tika evidence without normalizing raw MIME."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import base64
import subprocess
from pathlib import Path

from scripts.conformance.tika_contract import EXPERIMENT, MODES, SCHEMA_VERSION, TIKA_SHA512, TIKA_VERSION

PAIRS = tuple(("tika", mode) for mode in MODES) + (("magic", "content"),)
OS_BY_RUNNER = {"ubuntu-x64": "Linux", "macos-x64": "Darwin", "windows-x64": "Windows"}
JAVA_IDENTITY = ("java_version", "java_runtime_version", "java_vendor", "detector_config")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def _load(raw: bytes):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def _strings(value, *, nonempty=False):
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(isinstance(item, str) and bool(item.strip()) for item in value))


def _index(rows, key, errors, context):
    indexed = {}
    if not isinstance(rows, list):
        errors.append(f"{context}: expected list")
        return indexed
    for number, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{context}[{number}]: expected object")
            continue
        identity = key(row)
        parts = identity if isinstance(identity, tuple) else (identity,)
        if not all(isinstance(part, str) and part.strip() for part in parts):
            errors.append(f"{context}[{number}]: invalid identity")
        elif identity in indexed:
            errors.append(f"{context}: duplicate {identity!r}")
        else:
            indexed[identity] = row
    return indexed


def checkout_identity(root: Path, revision: str) -> dict:
    """Bind coverage and source identity to independent checkout bytes, not results."""
    corpus, originals, records = {}, {}, {}
    for name, filename in (("candidates", "backend_inventory_candidates.json"), ("inventory", "backend_inventory.json")):
        path = root / "tests" / "truth" / filename
        raw = path.read_bytes()
        payload = _load(raw)
        if not isinstance(payload, dict) or payload.get("schema_version") != 2:
            raise ValueError(f"{path}: expected schema_version 2")
        problems = []
        records[name] = _index(payload.get("records"), lambda row: row.get("id"), problems, str(path))
        if problems or not records[name]:
            raise ValueError("; ".join(problems) or f"{path}: empty inventory")
        corpus[f"{name}_sha256"] = _sha(raw)
        originals[name] = {"path": str(path), "sha256": _sha(raw), "raw_text": raw.decode("utf-8"), "payload": payload}
    if not records["inventory"].keys() <= records["candidates"].keys():
        raise ValueError("authoritative IDs absent from candidates")
    samples = []
    for identity, candidate in records["candidates"].items():
        authoritative = records["inventory"].get(identity)
        if authoritative is not None and any(candidate.get(key) != authoritative.get(key) for key in ("fixture", "sha256", "ground_truth")):
            raise ValueError(f"candidate/authoritative mismatch: {identity}")
        samples.append({"id": identity, "fixture": candidate.get("fixture"), "sha256": candidate.get("sha256"),
                        "authoritative": authoritative is not None,
                        "ground_truth": authoritative.get("ground_truth") if authoritative is not None else None})
    sources = {key: _sha((root / "scripts" / "conformance" / filename).read_bytes())
               for key, filename in (("probe_sha256", "TikaProbe.java"), ("collector_sha256", "tika_collect.py"))}
    return {"revision": revision, "corpus": corpus, "sources": sources, "samples": samples, "original_inputs": originals}


def compare_artifacts(artifacts: list, expected_runners: list[str], trusted: dict) -> dict:
    """Return a complete decision; every validation error is fail-closed."""
    errors, runners, sample_maps, observation_maps = [], {}, {}, {}
    expected = _index(trusted.get("samples"), lambda row: row.get("id"), errors, "checkout samples")
    if not expected:
        errors.append("checkout has no candidate samples")
    if not expected_runners or len(set(expected_runners)) != len(expected_runners):
        errors.append("expected runner labels must be nonempty and distinct")
    if set(expected_runners) != set(OS_BY_RUNNER):
        errors.append("cross-OS proof requires ubuntu-x64, macos-x64, windows-x64")
    if not re.fullmatch(r"[0-9a-f]{40}", str(trusted.get("revision", ""))):
        errors.append("expected revision must be a full source SHA")
    for position, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"input {position}: expected object")
            continue
        label = artifact.get("runner_label")
        if not isinstance(label, str) or label not in expected_runners:
            errors.append(f"input {position}: unexpected runner {label!r}")
            continue
        if label in runners:
            errors.append(f"duplicate runner: {label}")
            continue
        runners[label] = artifact
        prefix = f"{label}: "
        if type(artifact.get("schema_version")) is not int or artifact.get("schema_version") != SCHEMA_VERSION or artifact.get("experiment") != EXPERIMENT:
            errors.append(prefix + "schema/experiment mismatch")
        if artifact.get("revision") != trusted.get("revision"):
            errors.append(prefix + "stale/mismatched source revision")
        if artifact.get("corpus") != trusted.get("corpus"):
            errors.append(prefix + "corpus digest mismatch")
        if not isinstance(artifact.get("errors"), list) or artifact["errors"]:
            errors.append(prefix + f"collection errors: {artifact.get('errors')!r}")
        runtime = artifact.get("runtime")
        if not isinstance(runtime, dict):
            errors.append(prefix + "missing runtime")
            runtime = {}
        if runtime.get("os") != OS_BY_RUNNER.get(label) or runtime.get("architecture") != "x86_64":
            errors.append(prefix + "actual OS/architecture does not match cloud matrix")
        required = (*JAVA_IDENTITY, "python", "libmagic_version", "probe_sha256", "collector_sha256")
        if any(not isinstance(runtime.get(key), str) or not runtime[key].strip() for key in required):
            errors.append(prefix + "missing runtime/source identity")
        if runtime.get("tika_version") != TIKA_VERSION or runtime.get("tika_sha512") != TIKA_SHA512:
            errors.append(prefix + "pinned Tika JAR identity mismatch")
        for key, digest in trusted.get("sources", {}).items():
            if runtime.get(key) != digest:
                errors.append(prefix + f"checkout source identity mismatch: {key}")
        samples = _index(artifact.get("samples"), lambda row: row.get("id"), errors, prefix + "samples")
        sample_maps[label] = samples
        if samples.keys() != expected.keys():
            errors.append(prefix + f"candidate coverage missing={sorted(expected.keys() - samples.keys())!r} extra={sorted(samples.keys() - expected.keys())!r}")
        for identity, sample in samples.items():
            baseline = expected.get(identity)
            if baseline is None:
                continue
            if any(sample.get(key) != value for key, value in baseline.items()) or type(sample.get("authoritative")) is not bool:
                errors.append(prefix + f"sample metadata/expected bytes mismatch: {identity}")
            expected_sha, actual_sha = sample.get("sha256"), sample.get("observed_sha256")
            if (not isinstance(actual_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", actual_sha)
                    or actual_sha != expected_sha or sample.get("integrity_match") is not True):
                errors.append(prefix + f"sample integrity failure: {identity}")
        observations = _index(artifact.get("observations"), lambda row: (row.get("id"), row.get("backend"), row.get("mode")), errors, prefix + "observations")
        observation_maps[label] = observations
        wanted = {(identity, backend, mode) for identity in expected for backend, mode in PAIRS}
        if observations.keys() != wanted:
            errors.append(prefix + f"observation coverage missing={sorted(wanted - observations.keys())!r} extra={sorted(observations.keys() - wanted)!r}")
        for key, row in observations.items():
            if (row.get("status") != "ok" or row.get("error") is not None
                    or not _strings(row.get("mime_types"), nonempty=True) or not _strings(row.get("extensions"))
                    or type(row.get("elapsed_ns")) is not int or row["elapsed_ns"] < 0):
                errors.append(prefix + f"invalid/error observation {key!r}: {row.get('error')!r}")
    if set(runners) != set(expected_runners):
        errors.append(f"runner coverage missing={sorted(set(expected_runners) - runners.keys())!r}")
    java_identities = {tuple(artifact.get("runtime", {}).get(key) for key in JAVA_IDENTITY)
                       for artifact in runners.values() if isinstance(artifact.get("runtime"), dict)
                       and all(isinstance(artifact["runtime"].get(key), str) for key in JAVA_IDENTITY)}
    if len(java_identities) != 1:
        errors.append("configured Java runtime/detector identities differ or are absent")
    rows, divergences, compatibility = [], [], []
    for identity in sorted(expected):
        for backend, mode in PAIRS:
            raw = {label: observation_maps.get(label, {}).get((identity, backend, mode)) for label in expected_runners}
            valid = all(isinstance(row, dict) and row.get("status") == "ok" and row.get("error") is None
                        and _strings(row.get("mime_types"), nonempty=True) and _strings(row.get("extensions")) for row in raw.values())
            mime_match = valid and len({tuple(row["mime_types"]) for row in raw.values()}) == 1
            extension_match = valid and len({tuple(sorted(set(row["extensions"]))) for row in raw.values()}) == 1
            result = {"id": identity, "backend": backend, "mode": mode, "mime_match": mime_match,
                      "extension_match": extension_match, "comparable": valid, "observations": raw}
            rows.append(result)
            if valid and (not mime_match or not extension_match):
                divergences.append(result)
            truth = expected[identity].get("ground_truth")
            if expected[identity].get("authoritative") and isinstance(truth, dict):
                for label, observation in raw.items():
                    sample = sample_maps.get(label, {}).get(identity, {})
                    if sample.get("observed_sha256") != expected[identity].get("sha256"):
                        continue
                    compatibility.append({"id": identity, "runner_label": label, "backend": backend, "mode": mode,
                                          "mime_compatible": bool(observation and observation.get("status") == "ok"
                                                                  and observation.get("error") is None and _strings(observation.get("mime_types"))
                                                                  and set(observation["mime_types"]) & set(truth.get("mime_types", []))),
                                          "observed_mime_types": observation.get("mime_types") if observation else None,
                                          "reviewed_mime_types": truth.get("mime_types")})
    tika_rows = [row for row in rows if row["backend"] == "tika"]
    magic_rows = [row for row in rows if row["backend"] == "magic"]
    tika_passed = bool(tika_rows) and all(row["mime_match"] and row["extension_match"] for row in tika_rows)
    modes = {mode: {"mime_parity": all(row["mime_match"] for row in tika_rows if row["mode"] == mode),
                    "extension_parity": all(row["extension_match"] for row in tika_rows if row["mode"] == mode),
                    "incomparable_rows": sum(not row["comparable"] for row in tika_rows if row["mode"] == mode)} for mode in MODES}
    passed = not errors and tika_passed
    return {"schema_version": SCHEMA_VERSION, "experiment": EXPERIMENT, "passed": passed,
            "cross_os_verified": passed, "validation_errors": errors, "expected_runners": expected_runners,
            "expected_identity": trusted, "inputs": artifacts, "rows": rows, "divergences": divergences,
            "incomparable_rows": [row for row in rows if not row["comparable"]],
            "tika": {"parity_passed": tika_passed, "modes": modes},
            "libmagic": {"gate_criterion": False,
                         "mime_divergences": sum(row["comparable"] and not row["mime_match"] for row in magic_rows),
                         "host_extension_divergences": sum(row["comparable"] and not row["extension_match"] for row in magic_rows),
                         "incomparable_rows": sum(not row["comparable"] for row in magic_rows)},
            "reviewed_label_compatibility": {"is_accuracy": False, "alias_normalization": False,
                                            "denominator_per_runner_mode": sum(row.get("authoritative") is True and all(sample_maps.get(label, {}).get(identity, {}).get("observed_sha256") == row.get("sha256") for label in expected_runners) for identity, row in expected.items()),
                                            "eligible_denominators": [{"runner_label": label, "backend": backend, "mode": mode,
                                                                       "eligible": sum(row["runner_label"] == label and row["backend"] == backend and row["mode"] == mode for row in compatibility)}
                                                                      for label in expected_runners for backend, mode in PAIRS], "rows": compatibility}}


def write_reports(report: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "tika-conformance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "tika-conformance.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["id", "backend", "mode", "runner_label", "comparable", "mime_match", "extension_match", "status", "mime_types", "extensions", "error"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in report.get("rows", []):
            for label, observation in row["observations"].items():
                observation = observation or {}
                writer.writerow({"id": row["id"], "backend": row["backend"], "mode": row["mode"], "runner_label": label,
                                 "comparable": row["comparable"], "mime_match": row["mime_match"], "extension_match": row["extension_match"],
                                 **{key: json.dumps(observation.get(key), ensure_ascii=False) for key in ("status", "mime_types", "extensions", "error")}})
    tika, magic = report.get("tika", {}), report.get("libmagic", {})
    reviewed_content = [row for row in report.get("reviewed_label_compatibility", {}).get("rows", [])
                        if row["backend"] == "tika" and row["mode"] == "content"]
    lines = ["# Apache Tika OS 비교", "", f"- 최종 판정: {'통과' if report['passed'] else '실패'}",
             f"- 실제 Linux/macOS/Windows x86_64 교차 검증: {'성립' if report['cross_os_verified'] else '미성립'}",
             f"- 검증 오류: {len(report.get('validation_errors', []))}건", "", "| Tika 모드 | 원시 MIME 일치 | 확장자 집합 일치 | 비교불가 |", "|---|---|---|---|"]
    for mode, result in tika.get("modes", {}).items():
        lines.append(f"| {mode} | {result['mime_parity']} | {result['extension_parity']} | {result['incomparable_rows']} |")
    lines.extend(["", f"- libmagic 원시 MIME 차이: {magic.get('mime_divergences', 0)}건; 호스트 확장자 차이: {magic.get('host_extension_divergences', 0)}건; 비교불가: {magic.get('incomparable_rows', 0)}건 (Tika 통과 기준 아님).",
                  f"- Tika content 원시 MIME 라벨 호환: {sum(row['mime_compatible'] for row in reviewed_content)}/{len(reviewed_content)}개 관측 (러너별 SHA 일치 검토 샘플만).",
                  "- 검토 라벨과의 원시 MIME 호환성은 SHA 일치 authoritative 샘플만 집계하며 실제 형식 정확도·별칭 동등성을 주장하지 않습니다.",
                  "- 원본 입력, 모든 원시 목록·오류·차이·라벨 호환성은 JSON에, 전체 비교 행은 CSV에 보존합니다."])
    (output_dir / "tika-conformance.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _input_evidence(path: Path, artifact: dict) -> dict:
    """Keep full sidecar content; never follow paths outside its evidence sibling."""
    provenance = artifact.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError(f"{path}: missing provenance")
    directory = provenance.get("evidence_dir")
    if not isinstance(directory, str) or Path(directory).name != directory or directory in (".", ".."):
        raise ValueError(f"{path}: unsafe evidence directory")
    base = (path.parent / directory).resolve()
    if base.parent != path.parent.resolve():
        raise ValueError(f"{path}: evidence directory escaped input parent")
    retained = {"errors": []}
    names = {"candidates": "backend_inventory_candidates.json", "inventory": "backend_inventory.json",
             "manifest": "manifest.tsv", "java_stdout": "java.stdout", "java_stderr": "java.stderr", "run": "run.json"}
    for key, filename in names.items():
        try:
            if provenance.get(key) != filename:
                raise ValueError(f"{path}: invalid provenance filename for {key}")
            child = (base / filename).resolve()
            if child.parent != base:
                raise ValueError(f"{path}: escaped evidence file")
            raw = child.read_bytes()
            retained[key] = {"path": str(child), "sha256": _sha(raw), "raw_base64": base64.b64encode(raw).decode("ascii"),
                             "raw_text": raw.decode("utf-8", errors="replace")}
            corpus = artifact.get("corpus")
            if key in ("candidates", "inventory") and (not isinstance(corpus, dict) or _sha(raw) != corpus.get(f"{key}_sha256")):
                raise ValueError(f"{path}: retained {key} digest mismatch")
        except (OSError, ValueError) as exc:
            retained["errors"].append(str(exc))
    return retained


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--expected-runner", action="append", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-revision", help="Expected full source SHA; defaults to this checkout HEAD")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    errors, artifacts, input_artifacts = [], [], []
    trusted = {"samples": []}
    try:
        revision = args.expected_revision or subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
        trusted = checkout_identity(root, revision)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        errors.append(f"checkout identity: {exc}")
    for path in args.input:
        retained = {"path": str(path)}
        input_artifacts.append(retained)
        try:
            raw = path.read_bytes()
            retained.update({"sha256": _sha(raw), "raw_base64": base64.b64encode(raw).decode("ascii"),
                             "raw_text": raw.decode("utf-8", errors="replace")})
            artifact = _load(raw)
            if not isinstance(artifact, dict):
                raise ValueError("input is not an object")
            artifacts.append(artifact)
            retained["payload"] = artifact
            retained["evidence"] = _input_evidence(path, artifact)
            errors.extend(retained["evidence"]["errors"])
        except (OSError, ValueError, TypeError) as exc:
            retained["error"] = str(exc)
            errors.append(f"input {path}: {exc}")
    report = compare_artifacts(artifacts, args.expected_runner, trusted)
    report["input_artifacts"] = input_artifacts
    report["validation_errors"].extend(errors)
    if errors:
        report["passed"] = report["cross_os_verified"] = False
    write_reports(report, args.output_dir)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
