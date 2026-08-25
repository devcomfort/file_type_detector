"""Tests for MIME alias resolution and match-level evaluation."""

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
    assert (
        canonical_mime("application/vnd.debian.binary-package")
        == "application/vnd.debian.binary-package"
    )


def test_canonical_passes_through_unknown():
    assert canonical_mime("image/png") == "image/png"


# Q. Does the alias-aware evaluator pass a deb detected as x-debian-package when GT says vnd.debian.binary-package?
def test_deb_alias_match():
    sem = semantic_output(
        mime_types=["application/x-debian-package"], extensions=[".deb"]
    )
    gt = _gt(["application/vnd.debian.binary-package"], [".deb"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["overall_match"] is True
    assert result["match_level"] == "exact"


# Q. Does container-level match NOT count as overall_match?
def test_container_match_not_overall():
    sem = semantic_output(mime_types=["application/zip"], extensions=[".apk"])
    gt = _gt(["application/vnd.android.package-archive"], [".apk"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["match_level"] == "container"
    assert result["mime_match"] is False
    assert result["overall_match"] is False


# Q. Is audio/3gpp vs video/3gpp treated as a miss (not an alias)?
def test_3gpp_not_alias():
    sem = semantic_output(mime_types=["audio/3gpp"], extensions=[".3gp"])
    gt = _gt(["video/3gpp"], [".3gp"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["match_level"] == "miss"
    assert result["overall_match"] is False


# Q. Does exact match still work for direct hits?
def test_exact_match():
    sem = semantic_output(mime_types=["application/pdf"], extensions=[".pdf"])
    gt = _gt(["application/pdf"], [".pdf"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="ok")
    assert result["overall_match"] is True
    assert result["match_level"] == "exact"


# Q. Does non-ok status produce all-False?
def test_no_result_all_false():
    sem = semantic_output(mime_types=[], extensions=[])
    gt = _gt(["text/plain"], [".txt"])
    result = evaluate_output(semantic=sem, ground_truth=gt, status="no_result")
    assert result["overall_match"] is False
    assert result["match_level"] == "miss"
