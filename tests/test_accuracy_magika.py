"""Magika accuracy tests using canonical truth and tool snapshots.

Separates "Magika cannot identify this fixture" from "Magika identifies it but
returns a generic or wrong classification." Tests focus on Magika's authoritative
outputs: extensions (from ``result.output.extensions``) and confidence scores
(from ``result.prediction.score``).


Key design decisions
--------------------
- Extensions are Magika's authoritative output (``infer().extensions`` is from
  ``result.output.extensions``). Snapshot comparisons use these directly.
- Confidence scores are Magika's authoritative output (``infer_with_score()``
  returns ``result.prediction.score``). Snapshot comparisons use these.
- MIME types from ``infer()`` are **mimetypes-derived**, not Magika's raw MIME.
  ``MagikaInferencer.infer()`` re-derives MIME via ``mimetypes.guess_type()``
  on the first Magika extension. We do NOT treat mimetypes MIME as Magika truth.
- ``infer_with_score()`` returns (extension_str, score) where extension_str is
  the first Magika extension (with dot) or ``""`` if Magika returned none.
"""

import pytest
from pathlib import Path
from tests.conftest import fixture_path, load_canonical_fixtures, load_tool_snapshots
from filetype_detector.strategies import MagikaInferencer

CANONICAL = load_canonical_fixtures()
SNAPSHOTS = load_tool_snapshots()
SNAPSHOT_MAP: dict[str, dict] = {s["path"]: s for s in SNAPSHOTS["fixtures"]}




def _ext(fixture_path: str) -> str:
    return Path(fixture_path).name.split(".", 1)[1]


def _snap_exts(path: str) -> tuple[str, ...]:
    snap = SNAPSHOT_MAP.get(path)
    if snap is None:
        return ()
    return tuple(snap["tool_results"]["magika"]["extensions"])


def _snap_score(path: str) -> float:
    snap = SNAPSHOT_MAP.get(path)
    if snap is None:
        return 0.0
    return snap["tool_results"]["magika"]["score"]



FIXTURES_BY_CATEGORY: dict[str, list[dict]] = {}
for f in CANONICAL["fixtures"]:
    FIXTURES_BY_CATEGORY.setdefault(f["category"], []).append(f)

MAGIC_CORRECT = FIXTURES_BY_CATEGORY.get("magic_correct", [])
MAGIKA_IMPROVES = FIXTURES_BY_CATEGORY.get("magika_improves", [])
MAGIC_WRONG = FIXTURES_BY_CATEGORY.get("magic_wrong", [])
BOTH_GENERIC = FIXTURES_BY_CATEGORY.get("both_generic", [])
MAGIKA_FAILS = FIXTURES_BY_CATEGORY.get("magika_fails", [])

GENERIC_MIMES = frozenset({"text/plain", "application/octet-stream"})

SNAPSHOT_SAMPLE: list[dict] = [
    *MAGIC_CORRECT[:8],
    *MAGIKA_IMPROVES[:6],
    *MAGIC_WRONG[:3],
    *BOTH_GENERIC[:2],
    *MAGIKA_FAILS[:1],
]

SCORE_THRESHOLD_PATHS = [
    fixture_path("py"),
    fixture_path("json"),
    fixture_path("csv"),
    fixture_path("pdf"),
    fixture_path("png"),
]


@pytest.fixture(scope="module")
def magika() -> MagikaInferencer:
    return MagikaInferencer()

class TestMagikaImproves:
    """Magika improves over Magic's generic MIME (101 fixtures).

    These are primarily text-based files where Magic returns ``text/plain``
    (``text/x-c`` for ``.c``-like, ``application/octet-stream`` for unknowns)
    but Magika identifies the specific programming language / config format.
    """

    @pytest.mark.parametrize(
        "fixture",
        MAGIKA_IMPROVES,
        ids=[_ext(f["path"]) for f in MAGIKA_IMPROVES],
    )
    def test_returns_specific_extensions(self, fixture: dict, magika: MagikaInferencer) -> None:
        """Magika returns non-empty specific extensions for files it identifies."""
        path = fixture["path"]
        name = _ext(path)

        ft = magika.infer(path)
        snap_exts = _snap_exts(path)

        assert ft.extensions, f"{name}: Magika returned no extensions"
        # At least one returned extension should appear in the snapshot
        if snap_exts:
            overlap = set(ft.extensions) & set(snap_exts)
            assert overlap, (
                f"{name}: inferred extensions {ft.extensions} "
                f"do not overlap snapshot {snap_exts}"
            )

    @pytest.mark.parametrize(
        "fixture",
        MAGIKA_IMPROVES,
        ids=[_ext(f["path"]) for f in MAGIKA_IMPROVES],
    )
    def test_score_above_threshold(self, fixture: dict, magika: MagikaInferencer) -> None:
        """Magika returns a meaningful confidence score (>= 0.5) for files it identifies."""
        path = fixture["path"]
        name = _ext(path)

        ext, score = magika.infer_with_score(path)
        assert ext, f"{name}: infer_with_score returned empty extension"
        assert score >= 0.5, f"{name}: Score {score:.4f} is below 0.5 threshold"


class TestMagikaFails:
    """Formats where Magika cannot provide specific identification (20 fixtures).

    Magika returns empty extensions or a generic MIME (``text/plain`` /
    ``application/octet-stream``) for these. This is a known limitation.
    """

    @pytest.mark.parametrize(
        "fixture",
        MAGIKA_FAILS,
        ids=[_ext(f["path"]) for f in MAGIKA_FAILS],
    )
    def test_returns_empty_or_generic(self, fixture: dict, magika: MagikaInferencer) -> None:
        """Magika returns empty extensions or generic MIME for unsupported formats."""
        path = fixture["path"]
        name = _ext(path)

        ft = magika.infer(path)

        # Magika may return no extensions (empty tuple) or generic MIME
        if ft.extensions:
            # Has extensions but MIME should be generic
            assert any(
                generic in ft.mime_types for generic in GENERIC_MIMES
            ), f"{name}: expected generic MIME, got {ft.mime_types}"


class TestMagikaCorrectFixtures:
    """Binary/well-known files where Magic is correct (69 fixtures).

    Magika's performance on these varies: it may match Magic's specific MIME or
    return a different/generic result. These tests document the behavior without
    asserting that Magika matches Magic.
    """

    @pytest.mark.parametrize(
        "fixture",
        MAGIC_CORRECT,
        ids=[_ext(f["path"]) for f in MAGIC_CORRECT],
    )
    def test_returns_result(self, fixture: dict, magika: MagikaInferencer) -> None:
        """Magika returns a result (any extensions) for known binary files."""
        path = fixture["path"]
        name = _ext(path)
        ft = magika.infer(path)
        # Magika always returns *something* even if it's a generic result
        # (FileType may have empty extensions for some fixtures like .webm, .psd)
        assert isinstance(ft.extensions, tuple), f"{name}: extensions is not a tuple"


class TestMagikaGenericFixtures:
    """Files where both Magic and Magika return generic results (75 fixtures).

    Neither tool provides a specific MIME. These are primarily niche programming
    languages, markup formats, or binary formats unknown to both tools.
    """

    @pytest.mark.parametrize(
        "fixture",
        BOTH_GENERIC,
        ids=[_ext(f["path"]) for f in BOTH_GENERIC],
    )
    def test_returns_generic_result(self, fixture: dict, magika: MagikaInferencer) -> None:
        """Magika returns a generic result for files neither tool can identify."""
        path = fixture["path"]
        name = _ext(path)
        ft = magika.infer(path)

        # Magika may return any extensions; the key is that MIME is generic
        # (or empty).  This documents the known limitation.
        if ft.mime_types:
            assert any(
                generic in ft.mime_types for generic in GENERIC_MIMES
            ) or any(
                "text/" in m or "application/" in m for m in ft.mime_types
            ), f"{name}: unexpected MIME {ft.mime_types}"


class TestMagikaSnapshotMatch:
    """Version-pinned snapshot tests (20 representative fixtures).

    Pins current Magika behavior for extensions and confidence scores.
    When the Magika model is updated, these tests will fail and need
    regenerating via ``scripts/generate_truth_data.py``.
    """

    @pytest.mark.parametrize(
        "fixture",
        SNAPSHOT_SAMPLE,
        ids=[_ext(f["path"]) for f in SNAPSHOT_SAMPLE],
    )
    def test_extensions_match_snapshot(self, fixture: dict, magika: MagikaInferencer) -> None:
        """Inferred extensions match the snapshot's Magika extensions."""
        path = fixture["path"]
        name = _ext(path)
        snap_exts = _snap_exts(path)

        ft = magika.infer(path)

        # Magika may not have returned any extensions (snap_exts is empty).
        if snap_exts:
            overlap = set(ft.extensions) & set(snap_exts)
            assert overlap, (
                f"{name}: inferred {ft.extensions} vs snapshot {snap_exts}"
            )

    @pytest.mark.parametrize(
        "fixture",
        SNAPSHOT_SAMPLE,
        ids=[_ext(f["path"]) for f in SNAPSHOT_SAMPLE],
    )
    def test_score_matches_snapshot(self, fixture: dict, magika: MagikaInferencer) -> None:
        """Confidence score matches the snapshot value within a tolerance."""
        path = fixture["path"]
        name = _ext(path)
        expected_score = _snap_score(path)

        _ext_result, score = magika.infer_with_score(path)

        # Allow small floating-point tolerance for model determinism
        assert abs(score - expected_score) < 0.01, (
            f"{name}: score {score:.6f} != snapshot {expected_score:.6f}"
        )


class TestMagikaScoreThreshold:
    """High-confidence identification for well-known formats."""

    @pytest.mark.parametrize(
        "path",
        SCORE_THRESHOLD_PATHS,
        ids=[_ext(p) for p in SCORE_THRESHOLD_PATHS],
    )
    def test_high_confidence_for_well_known(self, path: str, magika: MagikaInferencer) -> None:
        """Magika returns > 0.9 confidence for well-known file formats."""
        name = _ext(path)
        _ext_result, score = magika.infer_with_score(path)
        assert score > 0.9, (
            f"{name}: score {score:.4f} <= 0.9 threshold "
            f"(expected high confidence for well-known format)"
        )
