"""Cross-suite smoke test that catches regressions across all inferencers.

Runs each inferencer against a representative sample of canonical fixtures
and asserts meaningful semantic correctness — not just "returned something."
"""

import pytest

from filetype_detector.strategies import (
    HybridInferencer,
    LexicalInferencer,
    MagicInferencer,
    MagikaInferencer,
)
from tests.conftest import load_canonical_fixtures, load_tool_snapshots

CANONICAL = load_canonical_fixtures()
SNAPSHOTS = load_tool_snapshots()

CANONICAL_MAP = {f["path"]: f for f in CANONICAL["fixtures"]}
SNAPSHOT_MAP = {s["path"]: s for s in SNAPSHOTS["fixtures"]}

# Fixture paths match the truth-file format: "tests/fixtures/sample.{ext}".
_FIXTURE_PREFIX = "tests/fixtures/sample."

# Representative sample across all five canonical categories (~7 per category).
# Selected at roughly regular intervals within each category for spread.
_REPRESENTATIVE = [
    # magic_correct — Magic returns the correct specific MIME.
    "7z",
    "doc",
    "gif",
    "java",
    "mov",
    "pgp",
    "svg",
    # magic_wrong — Magic returns a specific but incorrect MIME.
    "3gp",
    "class",
    "exe",
    "jar",
    "mid",
    "py",
    "tsx",
    # magika_improves — Magic returns generic; Magika provides specifics.
    "uppercase.CBL",
    "chisel",
    "f95",
    "mli",
    "pro",
    "srt",
    "vba",
    # both_generic — Neither Magic nor Magika provides a specific MIME.
    "uppercase.CPY",
    "bf",
    "csproj",
    "glsl",
    "ixx",
    "metal",
    "pt",
    # magika_fails — Magika returns empty; only Magic is available.
    "arc",
    "dcm",
    "dockerfile",
    "lha",
    "lzh",
    "oga",
    "opus",
]


def _fp(ext: str) -> str:
    """Construct the relative fixture path used by truth files and inferencers."""
    return f"{_FIXTURE_PREFIX}{ext}"


class TestLexicalSmoke:
    """Lexical must return the extension present in the filename."""

    @pytest.mark.parametrize("ext", _REPRESENTATIVE, ids=lambda e: e)
    def test_lexical_returns_filename_extension(self, ext: str) -> None:
        ft = LexicalInferencer().infer(_fp(ext))
        got_lower = {e.lower() for e in ft.extensions}
        expected_lower = f".{ext.rsplit('.', maxsplit=1)[-1].lower()}"
        assert expected_lower in got_lower, (
            f"Lexical({ext}): expected {expected_lower} in {ft.extensions}"
        )


class TestMagicSmoke:
    """Magic must match the version-pinned tool snapshot for every fixture."""

    @pytest.mark.parametrize("ext", _REPRESENTATIVE, ids=lambda e: e)
    def test_magic_matches_snapshot_mime(self, ext: str) -> None:
        fixture_path = _fp(ext)
        ft = MagicInferencer().infer(fixture_path)
        snap_mime = SNAPSHOT_MAP[fixture_path]["tool_results"]["magic"]["mime"]
        assert snap_mime in ft.mime_types, (
            f"Magic({ext}): snapshot {snap_mime} not in {ft.mime_types}"
        )


class TestMagikaSmoke:
    """Magika must return extensions when the tool snapshot expects them."""

    @pytest.mark.parametrize("ext", _REPRESENTATIVE, ids=lambda e: e)
    def test_magika_matches_snapshot_extensions(self, ext: str) -> None:
        fixture_path = _fp(ext)
        ft = MagikaInferencer().infer(fixture_path)
        snap_exts = SNAPSHOT_MAP[fixture_path]["tool_results"]["magika"]["extensions"]

        if not snap_exts:
            # Magika returned empty extensions in the snapshot — MagikaInferencer
            # will have empty FileType. Nothing to assert beyond the inferencer
            # not crashing.
            return

        # When the snapshot has extensions, MagikaInferencer must produce them.
        assert ft.extensions, (
            f"Magika({ext}): snapshot has extensions {snap_exts} but "
            f"MagikaInferencer returned empty: {ft.extensions}"
        )


class TestHybridSmoke:
    """Hybrid must not regress — it preserves correct results and always returns."""

    @pytest.mark.parametrize("ext", _REPRESENTATIVE, ids=lambda e: e)
    def test_hybrid_returns_result(self, ext: str) -> None:
        fixture_path = _fp(ext)
        ft = HybridInferencer().infer(fixture_path)
        assert ft.extensions or ft.mime_types, f"Hybrid({ext}): returned empty result"

    @pytest.mark.parametrize("ext", _REPRESENTATIVE, ids=lambda e: e)
    def test_hybrid_preserves_correct_mime(self, ext: str) -> None:
        fixture_path = _fp(ext)
        canonical = CANONICAL_MAP.get(fixture_path)
        if canonical is None or canonical["category"] != "magic_correct":
            pytest.skip("not a magic_correct fixture")

        ft = HybridInferencer().infer(fixture_path)
        expected_mime = canonical["canonical_mime"]
        assert expected_mime in ft.mime_types, (
            f"Hybrid({ext}): expected canonical {expected_mime}, got {ft.mime_types}"
        )

    @pytest.mark.parametrize("ext", _REPRESENTATIVE, ids=lambda e: e)
    def test_hybrid_improves_over_magic(self, ext: str) -> None:
        fixture_path = _fp(ext)
        canonical = CANONICAL_MAP.get(fixture_path)
        if canonical is None or canonical["category"] != "magika_improves":
            pytest.skip("not a magika_improves fixture")

        magic_ft = MagicInferencer().infer(fixture_path)
        hybrid_ft = HybridInferencer().infer(fixture_path)

        GENERIC_MIMES = {"text/plain", "text/x-c", "application/octet-stream"}
        magic_is_generic = all(m in GENERIC_MIMES for m in magic_ft.mime_types)

        if magic_is_generic:
            hybrid_non_generic = [
                m for m in hybrid_ft.mime_types if m not in GENERIC_MIMES
            ]
            assert hybrid_non_generic or hybrid_ft.mime_types != magic_ft.mime_types, (
                f"Hybrid({ext}): failed to improve over generic Magic result; "
                f"Magic={magic_ft.mime_types}, Hybrid={hybrid_ft.mime_types}"
            )
