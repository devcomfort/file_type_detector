"""Collect raw Tika and native libmagic evidence without production imports.

Java source-launch mode uses one pinned JAR and identical options on every OS.
The strict TSV protocol Base64-encodes variable output text; retained subprocess
streams are bytes, so Windows CRLF and full exception traces remain untouched.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import mimetypes
import os
import platform
import re
import subprocess
import tempfile
import time
import traceback
import urllib.request
from pathlib import Path, PurePosixPath

from scripts.conformance.tika_contract import (
    EXPERIMENT, MODES, SCHEMA_VERSION, TIKA_SHA512, TIKA_URL, TIKA_VERSION,
)

JAVA_OPTIONS = (
    "-Dfile.encoding=UTF-8", "-Duser.language=en", "-Duser.country=US", "-Duser.timezone=UTC",
)
DETECTOR_CONFIG = (
    "DefaultDetector;MimeTypes.getDefaultMimeTypes;fresh-Metadata;content-no-name;"
    "named-basename;wrong_pdf=payload.pdf;wrong_txt=payload.txt;tsv-base64-v1;"
    + ";".join(JAVA_OPTIONS)
)
_SOURCE = Path(__file__).resolve()
_PROBE = _SOURCE.with_name("TikaProbe.java")


def digest(path: Path, algorithm: str = "sha256") -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def ensure_jar(jar: Path, *, download: bool = False) -> None:
    """Verify before any Java execution; never replace an existing wrong JAR."""
    if jar.exists():
        if digest(jar, "sha512") != TIKA_SHA512:
            raise ValueError(f"JAR SHA512 mismatch: {jar}")
        return
    if not download:
        raise ValueError(f"JAR absent (use --download explicitly): {jar}")
    jar.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=jar.parent, suffix=".download", delete=False) as target:
            temporary = Path(target.name)
            with urllib.request.urlopen(TIKA_URL, timeout=120) as source:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
        if digest(temporary, "sha512") != TIKA_SHA512:
            raise ValueError("downloaded JAR SHA512 mismatch")
        if jar.exists():
            raise ValueError(f"refusing to overwrite concurrently created JAR: {jar}")
        os.replace(temporary, jar)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError(f"invalid {label}")
    return value


def _document(raw: bytes, root: Path, *, authoritative: bool = False) -> dict:
    document = json.loads(raw, object_pairs_hook=_unique_object)
    if (not isinstance(document, dict) or type(document.get("schema_version")) is not int
            or document["schema_version"] != 2):
        raise ValueError("inventory requires schema_version 2 object")
    records = document.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("inventory records must be nonempty list")
    indexed = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("inventory record must be object")
        sample_id = _text(record.get("id"), "inventory ID")
        if sample_id in indexed:
            raise ValueError(f"duplicate inventory ID: {sample_id}")
        fixture = _text(record.get("fixture"), f"{sample_id} fixture")
        path = PurePosixPath(fixture)
        if (path.is_absolute() or path.as_posix() != fixture or ".." in path.parts
                or "\\" in fixture or ":" in fixture or fixture == "."
                or not (root / fixture).resolve().is_relative_to(root)):
            raise ValueError(f"unsafe fixture path: {fixture}")
        if not isinstance(record.get("sha256"), str) or not re.fullmatch("[0-9a-f]{64}", record["sha256"]):
            raise ValueError(f"invalid {sample_id} SHA256")
        truth = record.get("ground_truth")
        if not isinstance(truth, dict):
            raise ValueError(f"invalid {sample_id} ground truth")
        for axis in ("mime_types", "extensions"):
            values = truth.get(axis)
            if not isinstance(values, list) or any(not isinstance(x, str) or not x for x in values):
                raise ValueError(f"invalid {sample_id} {axis}")
            if authoritative and len(set(values)) != len(values):
                raise ValueError(f"duplicate {sample_id} {axis}")
        review = record.get("ground_truth_review")
        if not isinstance(review, dict) or not isinstance(review.get("status"), str):
            raise ValueError(f"invalid {sample_id} review")
        indexed[sample_id] = record
    return indexed


def load_samples(candidate_bytes: bytes, inventory_bytes: bytes, root: Path) -> list[dict]:
    candidates = _document(candidate_bytes, root)
    authoritative = _document(inventory_bytes, root, authoritative=True)
    verified = {key for key, value in candidates.items() if value["ground_truth_review"]["status"] == "verified"}
    if verified != authoritative.keys():
        raise ValueError("verified candidate and authoritative ID sets differ")
    for sample_id, record in authoritative.items():
        candidate = candidates[sample_id]
        if record["ground_truth_review"]["status"] != "verified" or any(
            record[key] != candidate[key] for key in ("fixture", "sha256", "ground_truth")
        ):
            raise ValueError(f"candidate-authoritative SHA/label mismatch: {sample_id}")
    samples = []
    for sample_id, record in candidates.items():
        sample = {"id": sample_id, "fixture": record["fixture"], "sha256": record["sha256"],
                  "observed_sha256": None, "authoritative": sample_id in authoritative,
                  "integrity_match": False,
                  "ground_truth": authoritative[sample_id]["ground_truth"] if sample_id in authoritative else None}
        try:
            sample["observed_sha256"] = digest(root / sample["fixture"])
            sample["integrity_match"] = sample["observed_sha256"] == sample["sha256"]
        except OSError:
            # Actual detector attempts still run, recording each backend's full error.
            pass
        samples.append(sample)
    return samples


class ProbeValidationError(ValueError):
    def __init__(self, message: str, runtime: dict, observations: list[dict]):
        super().__init__(message)
        self.runtime = runtime
        self.observations = observations


def _decode(value: str) -> str:
    return base64.b64decode(value, validate=True).decode("utf-8")


def parse_probe(raw: bytes, ids: list[str]) -> tuple[dict, list[dict]]:
    """Reject duplicate/missing/malformed rows, retaining every valid observation."""
    runtime, observations, errors, seen = {}, [], [], set()
    expected = {(sample_id, mode) for sample_id in ids for mode in MODES}
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeError as error:
        raise ProbeValidationError(str(error), runtime, observations) from error
    for number, line in enumerate(lines, 1):
        fields = line.split("\t")
        try:
            if fields[0] == "runtime" and len(fields) == 4:
                if runtime:
                    raise ValueError("duplicate runtime row")
                values = [_decode(x) for x in fields[1:]]
                if not all(values):
                    raise ValueError("empty Java runtime identity")
                runtime = dict(zip(("java_version", "java_runtime_version", "java_vendor"), values))
                continue
            if len(fields) != 8 or fields[0] != "observation":
                raise ValueError("malformed probe row")
            _, sample_id, mode, status, mime, extensions, error, elapsed = fields
            key = (sample_id, mode)
            if key not in expected or key in seen:
                raise ValueError("unknown or duplicate observation")
            mime, error = _decode(mime), _decode(error)
            extensions = [_decode(x) for x in extensions.split(",")] if extensions else []
            if not elapsed.isascii() or not elapsed.isdecimal():
                raise ValueError("invalid elapsed_ns")
            if status not in ("ok", "error") or (status == "ok" and (not mime or error)) or (
                status == "error" and (not error or mime or extensions)
            ) or any(not x for x in extensions) or len(set(extensions)) != len(extensions):
                raise ValueError("invalid observation outcome")
            observations.append({"id": sample_id, "backend": "tika", "mode": mode,
                                 "status": status, "mime_types": [mime] if mime else [],
                                 "extensions": extensions, "error": error or None, "elapsed_ns": int(elapsed)})
            seen.add(key)
        except (ValueError, UnicodeError, binascii.Error) as error:
            errors.append(f"probe line {number}: {error}")
    if not runtime:
        errors.append("missing Java runtime row")
    if seen != expected:
        errors.append(f"missing {len(expected - seen)} Tika observations")
    if errors:
        raise ProbeValidationError("; ".join(errors), runtime, observations)
    return runtime, observations


def _error(sample_id: str, backend: str, mode: str, message: str, elapsed: int = 0) -> dict:
    return {"id": sample_id, "backend": backend, "mode": mode, "status": "error",
            "mime_types": [], "extensions": [], "error": message, "elapsed_ns": elapsed}


def collect_magic(samples: list[dict], root: Path) -> tuple[list[dict], str]:
    observations = []
    try:
        import magic
        # Both pinned bindings expose the native C API; the Windows one has no version().
        native_version = str(magic.libmagic.magic_version())
        detector = magic.Magic(mime=True)
    except Exception:
        error = traceback.format_exc()
        return ([_error(s["id"], "magic", "content", error) for s in samples], "error: " + error)
    for sample in samples:
        start = time.perf_counter_ns()
        try:
            mime = detector.from_file(str(root / sample["fixture"]))
            if not isinstance(mime, str) or not mime:
                raise ValueError("libmagic returned empty/non-string MIME")
            observations.append({"id": sample["id"], "backend": "magic", "mode": "content",
                                 "status": "ok", "mime_types": [mime],
                                 "extensions": mimetypes.guess_all_extensions(mime, strict=False), "error": None,
                                 "elapsed_ns": time.perf_counter_ns() - start})
        except Exception:
            observations.append(_error(sample["id"], "magic", "content", traceback.format_exc(),
                                       time.perf_counter_ns() - start))
    return observations, native_version


def collect(*, root: Path, runner_label: str, jar: Path, revision: str, output: Path,
            download: bool = False, candidates: Path | None = None, inventory: Path | None = None) -> int:
    """Always save available evidence; return 1 on any error or byte mismatch."""
    root, output, jar = root.resolve(), output.resolve(), jar.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence = output.parent / (output.stem + ".evidence")
    evidence.mkdir(exist_ok=True)
    names = {"candidates": "backend_inventory_candidates.json", "inventory": "backend_inventory.json",
             "manifest": "manifest.tsv", "java_stdout": "java.stdout", "java_stderr": "java.stderr", "run": "run.json"}
    runtime = {"os": platform.system(), "architecture": {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}.get(platform.machine().lower(), platform.machine().lower()),
               "python": platform.python_version(), "java_version": None, "java_runtime_version": None,
               "java_vendor": None, "tika_version": TIKA_VERSION, "tika_sha512": TIKA_SHA512,
               "probe_sha256": digest(_PROBE), "collector_sha256": digest(_SOURCE),
               "detector_config": DETECTOR_CONFIG, "libmagic_version": "error: not attempted"}
    artifact = {"schema_version": SCHEMA_VERSION, "experiment": EXPERIMENT, "runner_label": runner_label,
                "revision": revision, "runtime": runtime, "corpus": {}, "samples": [], "observations": [],
                "errors": [], "provenance": {"evidence_dir": evidence.name, **names}}
    run = {"command": None, "returncode": None, "java_options": list(JAVA_OPTIONS)}
    for key in ("manifest", "java_stdout", "java_stderr"):
        (evidence / names[key]).write_bytes(b"")
    try:
        _text(runner_label, "runner label")
        if not re.fullmatch(r"[0-9a-f]{40,64}", revision):
            raise ValueError("revision must be source commit SHA")
        paths = (candidates or root / "tests/truth/backend_inventory_candidates.json",
                 inventory or root / "tests/truth/backend_inventory.json")
        originals = []
        for key, path in zip(("candidates", "inventory"), paths):
            raw = path.read_bytes()
            (evidence / names[key]).write_bytes(raw)
            artifact["corpus"][key + "_sha256"] = hashlib.sha256(raw).hexdigest()
            originals.append(raw)
        samples = load_samples(*originals, root)
        artifact["samples"] = samples
        for sample in samples:
            if not sample["integrity_match"]:
                artifact["errors"].append(f"fixture SHA256 mismatch or unreadable: {sample['id']}")
        manifest = "".join(f"{sample['id']}\t{_text(str(root / sample['fixture']), 'manifest path')}\n" for sample in samples)
        (evidence / names["manifest"]).write_bytes(manifest.encode("utf-8"))
        # Native magic is independent: save its observations even if Java cannot start.
        magic_observations, runtime["libmagic_version"] = collect_magic(samples, root)
        artifact["observations"].extend(magic_observations)
        ensure_jar(jar, download=download)
        command = ["java", *JAVA_OPTIONS, "--class-path", str(jar), str(_PROBE), str(evidence / names["manifest"])]
        run["command"] = command
        result = subprocess.run(command, capture_output=True, check=False)
        run["returncode"] = result.returncode
        (evidence / names["java_stdout"]).write_bytes(result.stdout)
        (evidence / names["java_stderr"]).write_bytes(result.stderr)
        try:
            java_runtime, observations = parse_probe(result.stdout, [sample["id"] for sample in samples])
        except ProbeValidationError as error:
            java_runtime, observations = error.runtime, error.observations
            artifact["errors"].append(str(error))
        runtime.update(java_runtime)
        artifact["observations"].extend(observations)
        if result.returncode:
            artifact["errors"].append(f"Java process exited {result.returncode}; see java.stderr")
    except Exception:
        artifact["errors"].append(traceback.format_exc())
    observed = {(o["id"], o["backend"], o["mode"]) for o in artifact["observations"]}
    for sample in artifact["samples"]:
        for backend, modes in (("tika", MODES), ("magic", ("content",))):
            for mode in modes:
                if (sample["id"], backend, mode) not in observed:
                    artifact["observations"].append(_error(sample["id"], backend, mode,
                                                           "observation unavailable; see artifact errors and raw streams"))
    (evidence / names["run"]).write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return int(bool(artifact["errors"]) or any(o["status"] != "ok" for o in artifact["observations"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--runner-label", required=True)
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--inventory", type=Path)
    return collect(**vars(parser.parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
