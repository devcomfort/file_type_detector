"""Tests for MIME alias resolution, subtype hierarchy, and match-level evaluation."""

import sys

sys.path.insert(0, ".")

from scripts.conformance.types import GroundTruth  # noqa: E402
from scripts.conformance.evaluator import (  # noqa: E402
    canonical_mime,
    evaluate_output,
    semantic_output,
)


def _gt(mimes, exts):
    return GroundTruth(mimes=tuple(mimes), extensions=tuple(exts))


def test_canonical_resolves_debian_alias():
    assert (
        canonical_mime("application/x-debian-package")
        == "application/vnd.debian.binary-package"
    )


# Q. Does the alias-aware evaluator pass a deb detected as x-debian-package?
def test_deb_alias_match():
    sem = semantic_output(
        mime_types=["application/x-debian-package"], extensions=[".deb"]
    )
    gt = _gt(["application/vnd.debian.binary-package"], [".deb"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["overall_match"] is True
    assert result["match_level"] == "alias"


# Q. Is container-level match NOT counted as overall_match?
def test_container_match_not_overall():
    sem = semantic_output(mime_types=["application/zip"], extensions=[".apk"])
    gt = _gt(["application/vnd.android.package-archive"], [".apk"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["match_level"] == "container"
    assert result["overall_match"] is False


# Q. Is audio/3gpp vs video/3gpp treated as a miss (not an alias)?
def test_3gpp_not_alias():
    sem = semantic_output(mime_types=["audio/3gpp"], extensions=[".3gp"])
    gt = _gt(["video/3gpp"], [".3gp"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["match_level"] == "miss"
    assert result["overall_match"] is False


# Q. Does exact match still work?
def test_exact_match():
    sem = semantic_output(mime_types=["application/pdf"], extensions=[".pdf"])
    gt = _gt(["application/pdf"], [".pdf"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["overall_match"] is True
    assert result["match_level"] == "exact"


# Q. Is x-x509-ca-cert → pkix-cert a SUBTYPE match (directional child→parent)?
def test_x509_subtype_directional_pass():
    # Backend detects x-x509-ca-cert (child), GT says pkix-cert (parent) → PASS
    sem = semantic_output(
        mime_types=["application/x-x509-ca-cert"], extensions=[".cer"]
    )
    gt = _gt(["application/pkix-cert"], [".cer"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["match_level"] == "subtype"
    assert result["overall_match"] is True


# Q. Is pkix-cert → x-x509-ca-cert a CONTAINER match (directional parent→child)?
def test_pkix_parent_detected_child_gt_is_container():
    # Backend detects pkix-cert (parent), GT says x-x509-ca-cert (child) → NOT overall
    sem = semantic_output(mime_types=["application/pkix-cert"], extensions=[".cer"])
    gt = _gt(["application/x-x509-ca-cert"], [".cer"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["match_level"] == "container"
    assert result["overall_match"] is False


# Q. Is x-x509-ca-cert removed from MIME_ALIASES (it's a subtype, not alias)?
def test_x509_not_in_alias_map():
    from scripts.conformance.evaluator import MIME_ALIASES

    assert "application/x-x509-ca-cert" not in MIME_ALIASES


# Q. Does non-ok status produce all-False?
def test_no_result_all_false():
    sem = semantic_output(mime_types=[], extensions=[])
    gt = _gt(["text/plain"], [".txt"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="no_result")
    assert result["overall_match"] is False
    assert result["match_level"] == "miss"
