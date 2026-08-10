"""Regression tests for portable fixture generation."""

from pathlib import Path

from scripts.generators.__main__ import write_sources_manifest
from scripts.generators.base import BaseGenerator

_CASE_VARIANT_EXTENSIONS = ["CBL", "COB", "CPY", "F90", "P", "R", "S"]
_EXPECTED_FILENAMES = [
    "sample.uppercase.CBL",
    "sample.uppercase.COB",
    "sample.uppercase.CPY",
    "sample.uppercase.F90",
    "sample.uppercase.P",
    "sample.uppercase.R",
    "sample.uppercase.S",
]


class _CaseVariantGenerator(BaseGenerator):
    @property
    def extensions(self) -> list[str]:
        return _CASE_VARIANT_EXTENSIONS

    def generate(self, ext: str) -> bytes:
        return ext.encode("ascii")


# Q. Does the shared generator path preserve case variants on every supported OS?
def test_generator_creates_portable_case_variant_filenames(tmp_path: Path) -> None:
    generator = _CaseVariantGenerator()
    created = [
        generator.create_fixture(tmp_path, ext, force=True)
        for ext in generator.extensions
    ]

    assert all(path is not None for path in created)
    filenames = [path.name for path in created if path is not None]
    assert filenames == _EXPECTED_FILENAMES
    assert len({filename.casefold() for filename in filenames}) == len(filenames)


# Q. Does SOURCES.md retain generated case variants as registered fixtures?
def test_sources_manifest_recognizes_portable_case_variants(tmp_path: Path) -> None:
    for filename in _EXPECTED_FILENAMES:
        (tmp_path / filename).write_bytes(b"fixture")

    write_sources_manifest(tmp_path)

    manifest = (tmp_path / "SOURCES.md").read_text(encoding="utf-8")
    assert "## Discovered fixtures (no registered generator)" not in manifest
    for filename in _EXPECTED_FILENAMES:
        assert f"`{filename}`" in manifest
