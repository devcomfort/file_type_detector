"""Consumer-visible failure evidence for the isolated Tika collector."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from scripts.conformance import tika_collect as collector
from scripts.conformance.tika_contract import MODES


def _encoded(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _probe_output(ids: list[str]) -> bytes:
    lines = ["runtime\t" + "\t".join(_encoded(x) for x in ("21", "21+1", "Vendor"))]
    lines.extend(
        f"observation\t{sample_id}\t{mode}\tok\t{_encoded('text/plain')}\t\t\t1"
        for sample_id in ids for mode in MODES
    )
    return ("\r\n".join(lines) + "\r\n").encode()


def _corpus(root: Path) -> None:
    fixture = root / "tests/fixtures/sample.txt"
    fixture.parent.mkdir(parents=True)
    fixture.write_bytes(b"hello\r\n")
    record = {
        "id": "sample-txt", "fixture": "tests/fixtures/sample.txt",
        "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "ground_truth": {"mime_types": ["text/plain"], "extensions": [".txt"]},
        "ground_truth_review": {"status": "verified"},
    }
    truth = root / "tests/truth"
    truth.mkdir()
    payload = json.dumps({"schema_version": 2, "records": [record]}).encode()
    for name in ("backend_inventory_candidates.json", "backend_inventory.json"):
        (truth / name).write_bytes(payload)


def test_invalid_jar_is_rejected_before_execution_and_retains_inputs(tmp_path, monkeypatch):
    _corpus(tmp_path)
    jar = tmp_path / "tika.jar"
    jar.write_bytes(b"not the pinned jar")
    monkeypatch.setattr(collector.subprocess, "run", lambda *a, **kw: pytest.fail("Java executed"))
    output = tmp_path / "result.json"
    assert collector.collect(root=tmp_path, runner_label="test", jar=jar,
                             revision="a" * 40, output=output) == 1
    artifact = json.loads(output.read_bytes())
    assert any("SHA512" in error for error in artifact["errors"])
    evidence = output.parent / artifact["provenance"]["evidence_dir"]
    assert (evidence / "backend_inventory_candidates.json").read_bytes() == (
        tmp_path / "tests/truth/backend_inventory_candidates.json"
    ).read_bytes()


@pytest.mark.parametrize("damage", ["malformed", "duplicate", "missing"])
def test_invalid_probe_observations_fail_closed(damage):
    rows = _probe_output(["sample-txt"]).decode().splitlines()
    if damage == "malformed":
        rows[1] = "observation\tsample-txt\tcontent\tok\t%%%\t\t\t1"
    elif damage == "duplicate":
        rows.append(rows[1])
    else:
        rows.pop()
    with pytest.raises(collector.ProbeValidationError):
        collector.parse_probe(("\r\n".join(rows) + "\r\n").encode(), ["sample-txt"])


def test_crlf_probe_and_empty_extensions_are_preserved():
    runtime, observations = collector.parse_probe(_probe_output(["sample-txt"]), ["sample-txt"])
    assert runtime["java_runtime_version"] == "21+1"
    assert len(observations) == 4
    assert observations[0]["mime_types"] == ["text/plain"]
    assert observations[0]["extensions"] == []


def test_hash_mismatch_emits_complete_evidence_with_nonzero_exit(tmp_path, monkeypatch):
    _corpus(tmp_path)
    (tmp_path / "tests/fixtures/sample.txt").write_bytes(b"changed\r\n")
    jar = tmp_path / "tika.jar"
    jar.write_bytes(b"test boundary only")
    monkeypatch.setattr(collector, "ensure_jar", lambda *a, **kw: None)
    raw = _probe_output(["sample-txt"])
    monkeypatch.setattr(collector.subprocess, "run", lambda *a, **kw: CompletedProcess(a, 0, raw, b"full\r\nstderr\r\n"))
    monkeypatch.setattr(collector, "collect_magic", lambda *a: ([{
        "id": "sample-txt", "backend": "magic", "mode": "content", "status": "ok",
        "mime_types": ["text/plain"], "extensions": [".txt"], "error": None, "elapsed_ns": 1,
    }], "test-native"))
    output = tmp_path / "result.json"
    assert collector.collect(root=tmp_path, runner_label="test", jar=jar,
                             revision="a" * 40, output=output) == 1
    artifact = json.loads(output.read_bytes())
    assert artifact["samples"][0]["integrity_match"] is False
    assert artifact["samples"][0]["sha256"] != artifact["samples"][0]["observed_sha256"]
    assert len(artifact["observations"]) == 5
    evidence = output.parent / artifact["provenance"]["evidence_dir"]
    assert (evidence / "java.stdout").read_bytes() == raw
    assert (evidence / "java.stderr").read_bytes() == b"full\r\nstderr\r\n"


def test_unreviewed_duplicate_labels_do_not_block_collection_or_change_originals(tmp_path, monkeypatch):
    _corpus(tmp_path)
    candidates = tmp_path / "tests/truth/backend_inventory_candidates.json"
    document = json.loads(candidates.read_bytes())
    candidate = dict(document["records"][0])
    candidate.update(id="unreviewed-txt", ground_truth_review={"status": "excluded"},
                     ground_truth={"mime_types": ["text/plain", "text/plain"],
                                   "extensions": [".txt", ".txt"]})
    document["records"].append(candidate)
    original = json.dumps(document).encode()
    candidates.write_bytes(original)
    ids = ["sample-txt", "unreviewed-txt"]
    monkeypatch.setattr(collector, "ensure_jar", lambda *a, **kw: None)
    monkeypatch.setattr(collector.subprocess, "run", lambda *a, **kw: CompletedProcess(a, 0, _probe_output(ids), b""))
    monkeypatch.setattr(collector, "collect_magic", lambda *a: ([{
        "id": sample_id, "backend": "magic", "mode": "content", "status": "ok",
        "mime_types": ["text/plain"], "extensions": [".txt"], "error": None, "elapsed_ns": 1,
    } for sample_id in ids], "test-native"))
    output = tmp_path / "result.json"
    assert collector.collect(root=tmp_path, runner_label="test", jar=tmp_path / "tika.jar",
                             revision="a" * 40, output=output) == 0
    artifact = json.loads(output.read_bytes())
    assert len(artifact["observations"]) == 10
    assert artifact["samples"][0]["ground_truth"] == {
        "mime_types": ["text/plain"], "extensions": [".txt"],
    }
    assert artifact["samples"][1]["ground_truth"] is None
    evidence = output.parent / artifact["provenance"]["evidence_dir"]
    assert (evidence / "backend_inventory_candidates.json").read_bytes() == original


def test_legacy_windows_binding_metadata_does_not_prevent_detection(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    legacy = SimpleNamespace(
        libmagic=SimpleNamespace(magic_version=lambda: 526),
        Magic=lambda **kwargs: SimpleNamespace(from_file=lambda path: "text/plain"),
    )
    monkeypatch.setitem(sys.modules, "magic", legacy)
    (tmp_path / "sample.txt").write_text("sample", encoding="utf-8")
    rows, native_version = collector.collect_magic(
        [{"id": "sample", "fixture": "sample.txt"}], tmp_path,
    )
    assert rows[0]["status"] == "ok"
    assert rows[0]["mime_types"] == ["text/plain"]
    assert native_version == "526"
