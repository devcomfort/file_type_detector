"""Magic inferencer accuracy tests.

Uses canonical fixture truth and tool snapshots to assert Magic's detection
contract. Semantic accuracy checks use canonical expectations; version-pinned
checks use the snapshot to guard against libmagic version drift.

Magic's documented limitations (text/x-c for C-like, text/plain for unknown
text, application/octet-stream for unknown binary) are explicitly tested.
"""

import pytest
from pathlib import Path
from tests.conftest import fixture_path, load_canonical_fixtures, load_tool_snapshots
from filetype_detector.strategies import MagicInferencer

CANONICAL = load_canonical_fixtures()
SNAPSHOTS = load_tool_snapshots()

SNAPSHOT_MAP = {s["path"]: s for s in SNAPSHOTS["fixtures"]}
CANONICAL_MAP = {f["path"]: f for f in CANONICAL["fixtures"]}

GENERIC_MIMES = {"text/plain", "text/x-c", "application/octet-stream"}


def _ext(path: str) -> str:
    """Extract the extension from a canonical fixture path like ``sample.txt`` → ``txt``."""
    # Path("sample.txt").name → "sample.txt"
    return Path(path).name.split(".", 1)[1]


class TestMagicAccuracy:
    """Semantic accuracy: what Magic CAN and CANNOT do."""

    @pytest.mark.parametrize(
        "fixture_path",
        [f["path"] for f in CANONICAL["fixtures"] if f["category"] == "magic_correct"],
        ids=lambda p: _ext(p),
    )
    def test_magic_correct_fixtures(self, fixture_path: str) -> None:
        """Magic returns the correct MIME for magic_correct fixtures."""
        ft = MagicInferencer().infer(fixture_path)
        expected = CANONICAL_MAP[fixture_path]["canonical_mime"]
        assert expected in ft.mime_types, (
            f"{fixture_path}: expected {expected} in {ft.mime_types}"
        )

    @pytest.mark.parametrize(
        "fixture_path",
        [f["path"] for f in CANONICAL["fixtures"] if f["category"] == "both_generic"],
        ids=lambda p: _ext(p),
    )
    def test_magic_generic_fixtures(self, fixture_path: str) -> None:
        """Magic returns a known generic MIME for both_generic fixtures."""
        ft = MagicInferencer().infer(fixture_path)
        # At least one returned MIME should be in the generic set
        assert any(m in GENERIC_MIMES for m in ft.mime_types), (
            f"{fixture_path}: expected a generic MIME in {ft.mime_types}"
        )

    @pytest.mark.parametrize(
        "fixture_path",
        [
            s["path"]
            for i, s in enumerate(SNAPSHOTS["fixtures"])
            if i % 20 == 0  # every 20th → ~20 fixtures
        ],
        ids=lambda p: _ext(p),
    )
    def test_magic_snapshot_match(self, fixture_path: str) -> None:
        """Magic output matches pinned snapshot for a representative sample."""
        ft = MagicInferencer().infer(fixture_path)
        snap = SNAPSHOT_MAP[fixture_path]
        snap_mime = snap["tool_results"]["magic"]["mime"]
        assert snap_mime in ft.mime_types, (
            f"{fixture_path}: snapshot {snap_mime} not in {ft.mime_types}"
        )

    @pytest.mark.parametrize(
        "fixture_path",
        [s["path"] for s in SNAPSHOTS["fixtures"]],
        ids=lambda p: _ext(p),
    )
    def test_magic_never_returns_none(self, fixture_path: str) -> None:
        """Magic returns a non-None MIME for ALL fixtures (verified via snapshot)."""
        ft = MagicInferencer().infer(fixture_path)
        snap = SNAPSHOT_MAP[fixture_path]
        snap_mime = snap["tool_results"]["magic"]["mime"]
        # Prove non-None by matching against snapshot (not bare truthiness)
        assert snap_mime in ft.mime_types, (
            f"{fixture_path}: snapshot {snap_mime} not in {ft.mime_types}"
        )


class TestMagicKnownLimitations:
    """Explicitly documented limitations of libmagic detection."""

    @pytest.mark.parametrize(
        "ext",
        ["c", "cpp", "h", "cc"],
        ids=lambda e: f"sample.{e}",
    )
    def test_magic_text_c_is_generic(self, ext: str) -> None:
        """C/C++ source files return text/x-c (Magic cannot distinguish dialects)."""
        ft = MagicInferencer().infer(fixture_path(ext))
        assert "text/x-c" in ft.mime_types, (
            f"sample.{ext}: expected text/x-c in {ft.mime_types}"
        )

    @pytest.mark.parametrize(
        "ext",
        ["txt", "text", "md", "rst", "ini"],
        ids=lambda e: f"sample.{e}",
    )
    def test_magic_text_plain_is_generic(self, ext: str) -> None:
        """Plain-text files return text/plain (Magic cannot distinguish formats)."""
        ft = MagicInferencer().infer(fixture_path(ext))
        assert "text/plain" in ft.mime_types, (
            f"sample.{ext}: expected text/plain in {ft.mime_types}"
        )
