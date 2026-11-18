"""False-green regression cases for the isolated Tika comparison gate."""

from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.conformance.tika_compare import compare_artifacts, write_reports
from scripts.conformance.tika_contract import EXPERIMENT, MODES, SCHEMA_VERSION, TIKA_SHA512, TIKA_VERSION


@pytest.fixture
def evidence():
    sample = {"id": "sample", "fixture": "tests/fixtures/sample.txt", "sha256": "a" * 64,
              "authoritative": True, "ground_truth": {"mime_types": ["text/plain"], "extensions": [".txt"]}}
    trusted = {"revision": "b" * 40, "corpus": {"candidates_sha256": "c" * 64, "inventory_sha256": "d" * 64},
               "sources": {"probe_sha256": "e" * 64, "collector_sha256": "f" * 64}, "samples": [sample]}
    artifacts = []
    for label, os_name in (("ubuntu-x64", "Linux"), ("macos-x64", "Darwin"), ("windows-x64", "Windows")):
        artifacts.append({"schema_version": SCHEMA_VERSION, "experiment": EXPERIMENT, "runner_label": label,
                          "revision": trusted["revision"], "corpus": deepcopy(trusted["corpus"]), "errors": [],
                          "runtime": {"os": os_name, "architecture": "x86_64", "python": "3.12.10",
                                      "java_version": "21.0.10", "java_runtime_version": "21.0.10+7-LTS",
                                      "java_vendor": "Eclipse Adoptium", "tika_version": TIKA_VERSION,
                                      "tika_sha512": TIKA_SHA512, "detector_config": "test-exact-config",
                                      "libmagic_version": "546", **trusted["sources"]},
                          "samples": [{**deepcopy(sample), "observed_sha256": sample["sha256"], "integrity_match": True}],
                          "observations": [{"id": "sample", "backend": backend, "mode": mode, "status": "ok",
                                            "mime_types": ["text/plain"], "extensions": [".txt", ".text"],
                                            "error": None, "elapsed_ns": 10}
                                           for backend, mode in [("tika", m) for m in MODES] + [("magic", "content")]]})
    return artifacts, [a["runner_label"] for a in artifacts], trusted


def compare(evidence):
    artifacts, labels, trusted = evidence
    return compare_artifacts(artifacts, labels, trusted)


def test_full_raw_evidence_and_extension_order_survive(evidence, tmp_path):
    evidence[0][1]["observations"][0]["extensions"].reverse()
    report = compare(evidence)
    assert report["passed"] and report["cross_os_verified"]
    assert len(report["rows"]) == 5
    assert report["inputs"][1]["observations"][0]["extensions"] == [".text", ".txt"]
    write_reports(report, tmp_path)
    assert all((tmp_path / f"tika-conformance.{suffix}").exists() for suffix in ("json", "csv", "md"))


@pytest.mark.parametrize("missing", ["runner", "observation", "sample", "error"])
def test_missing_evidence_never_passes(evidence, missing, tmp_path):
    if missing == "runner":
        evidence[0].pop()
    elif missing == "observation":
        evidence[0][1]["observations"].pop()
    elif missing == "error":
        evidence[0][1]["observations"][-1].update(status="error", error="injected failure")
    else:
        for artifact in evidence[0]:
            artifact["samples"] = []
            artifact["observations"] = []
    report = compare(evidence)
    assert not report["passed"] and not report["cross_os_verified"]
    assert report["divergences"] == []
    assert report["libmagic"]["mime_divergences"] == 0
    assert report["libmagic"]["host_extension_divergences"] == 0
    assert report["libmagic"]["incomparable_rows"] == 1
    assert report["incomparable_rows"]
    write_reports(report, tmp_path)
    summary = (tmp_path / "tika-conformance.md").read_text(encoding="utf-8")
    assert "libmagic 원시 MIME 차이: 0건" in summary
    assert "호스트 확장자 차이: 0건; 비교불가: 1건" in summary


@pytest.mark.parametrize("duplicate", ["runner", "sample", "observation"])
def test_duplicates_never_collapse_to_a_green_dictionary(evidence, duplicate):
    if duplicate == "runner":
        evidence[0].append(deepcopy(evidence[0][0]))
    else:
        key = "samples" if duplicate == "sample" else "observations"
        evidence[0][0][key].append(deepcopy(evidence[0][0][key][0]))
    assert not compare(evidence)["passed"]


@pytest.mark.parametrize("identity", ["actual_sha", "revision", "uniform_stale_revision", "java_runtime_version", "probe_sha256", "tika_sha512"])
def test_mismatched_or_stale_identity_fails(evidence, identity):
    artifacts = evidence[0]
    if identity == "actual_sha":
        artifacts[1]["samples"][0]["observed_sha256"] = "0" * 64
    elif identity == "revision":
        artifacts[1]["revision"] = "0" * 40
    elif identity == "uniform_stale_revision":
        for artifact in artifacts:
            artifact["revision"] = "0" * 40
    else:
        artifacts[1]["runtime"][identity] = "different"
    report = compare(evidence)
    assert not report["passed"] and not report["cross_os_verified"]


@pytest.mark.parametrize("location", ["artifact", "observation", "ok_with_error"])
def test_injected_errors_are_preserved_and_fail(evidence, location):
    artifact = evidence[0][1]
    if location == "artifact":
        artifact["errors"] = ["injected failure"]
    else:
        artifact["observations"][0]["error"] = "injected failure"
        if location == "observation":
            artifact["observations"][0]["status"] = "error"
    report = compare(evidence)
    assert not report["passed"]
    assert "injected failure" in str(report["inputs"])


@pytest.mark.parametrize("field,value", [("mime_types", ["TEXT/PLAIN"]), ("mime_types", ["text/plain; charset=utf-8"]), ("extensions", [".other"])])
def test_tika_raw_mime_and_extension_drift_fail_separately(evidence, field, value):
    evidence[0][2]["observations"][1][field] = value
    report = compare(evidence)
    assert not report["passed"] and report["divergences"]
    row = next(row for row in report["rows"] if row["mode"] == "named" and row["backend"] == "tika")
    assert row["mime_match"] is (field != "mime_types")
    assert row["extension_match"] is (field != "extensions")


def test_libmagic_divergence_is_not_tika_failure_or_accuracy(evidence):
    evidence[0][2]["observations"][-1]["mime_types"] = ["application/octet-stream"]
    report = compare(evidence)
    assert report["passed"] and report["libmagic"]["mime_divergences"] == 1
    assert report["libmagic"]["incomparable_rows"] == 0
    assert report["reviewed_label_compatibility"]["is_accuracy"] is False
    assert report["reviewed_label_compatibility"]["denominator_per_runner_mode"] == 1


@pytest.mark.parametrize("field,value", [("os", "Linux"), ("architecture", "arm64")])
def test_labels_cannot_fake_the_actual_os_matrix(evidence, field, value):
    evidence[0][1]["runtime"][field] = value
    report = compare(evidence)
    assert not report["passed"] and not report["cross_os_verified"]
