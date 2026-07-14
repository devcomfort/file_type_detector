"""Tests for AutoInferencer — delegation correctness, error handling, and input flexibility."""

import pytest

from filetype_detector.auto_inferencer import AutoInferencer
from filetype_detector.strategies import (
    LexicalInferencer,
    MagicInferencer,
    MagikaInferencer,
    HybridInferencer,
)

DIRECT_INFERENCERS = {
    "lexical": LexicalInferencer,
    "magic": MagicInferencer,
    "magika": MagikaInferencer,
    "hybrid": HybridInferencer,
}

# Canonical fixture extensions used across delegation and semantic tests.
_CANONICAL_EXTS = ["pdf", "py", "json", "txt", "png", "zip"]


class TestDelegationCorrectness:
    """AutoInferencer(backend=X) must produce the identical result as XInferencer()."""

    @pytest.mark.parametrize(
        "backend, ext",
        [
            ("lexical", e) for e in _CANONICAL_EXTS
        ] + [
            ("magic", e) for e in _CANONICAL_EXTS
        ] + [
            ("magika", e) for e in _CANONICAL_EXTS
        ] + [
            ("hybrid", e) for e in _CANONICAL_EXTS
        ],
        ids=lambda p: f"{p[0]}-{p[1]}" if isinstance(p, tuple) else p,
    )
    def test_delegation_matches_direct_inferencer(self, backend: str, ext: str) -> None:
        fixture_path = f"tests/fixtures/sample.{ext}"
        direct_ft = DIRECT_INFERENCERS[backend]().infer(fixture_path)
        auto_ft = AutoInferencer(backend=backend).infer(fixture_path)
        assert direct_ft.extensions == auto_ft.extensions, (
            f"{backend}({ext}): ext mismatch — direct={direct_ft.extensions}, "
            f"auto={auto_ft.extensions}"
        )
        assert direct_ft.mime_types == auto_ft.mime_types, (
            f"{backend}({ext}): mime mismatch — direct={direct_ft.mime_types}, "
            f"auto={auto_ft.mime_types}"
        )


class TestPerBackendSemantics:
    """Semantic correctness of each backend through AutoInferencer on canonical fixtures."""

    @pytest.mark.parametrize(
        "backend, filename, expected_ext",
        [
            ("lexical", "document.pdf", ".pdf"),
            ("lexical", "script.py", ".py"),
            ("lexical", "data.json", ".json"),
        ],
    )
    def test_lexical_backend_returns_extension(
        self, backend: str, filename: str, expected_ext: str
    ) -> None:
        inferencer = AutoInferencer(backend=backend)
        ft = inferencer.infer(filename)
        assert expected_ext in ft.extensions

    def test_magic_backend_with_pdf(self, sample_pdf) -> None:
        ft = AutoInferencer(backend="magic").infer(sample_pdf)
        assert ".pdf" in ft.extensions
        assert "application/pdf" in ft.mime_types

    def test_magic_backend_with_python(self, sample_py) -> None:
        ft = AutoInferencer(backend="magic").infer(sample_py)
        assert ft.mime_types

    def test_magic_backend_with_json(self, sample_json) -> None:
        ft = AutoInferencer(backend="magic").infer(sample_json)
        assert "application/json" in ft.mime_types

    def test_magika_backend_with_pdf(self, sample_pdf) -> None:
        ft = AutoInferencer(backend="magika").infer(sample_pdf)
        assert ".pdf" in ft.extensions

    def test_magika_backend_with_python(self, sample_py) -> None:
        ft = AutoInferencer(backend="magika").infer(sample_py)
        assert ".py" in ft.extensions

    def test_magika_backend_with_json(self, sample_json) -> None:
        ft = AutoInferencer(backend="magika").infer(sample_json)
        assert ".json" in ft.extensions

    def test_hybrid_backend_with_pdf(self, sample_pdf) -> None:
        ft = AutoInferencer(backend="hybrid").infer(sample_pdf)
        assert ".pdf" in ft.extensions

    def test_hybrid_backend_with_python(self, sample_py) -> None:
        ft = AutoInferencer(backend="hybrid").infer(sample_py)
        assert ".py" in ft.extensions

    def test_hybrid_backend_with_json(self, sample_json) -> None:
        ft = AutoInferencer(backend="hybrid").infer(sample_json)
        assert ".json" in ft.extensions


class TestErrorHandling:
    """Exception cases use temp files/paths — the only purpose for temp test data."""

    @pytest.mark.parametrize("backend", ["magic", "magika", "hybrid"])
    def test_file_not_found_raises(self, backend: str) -> None:
        inferencer = AutoInferencer(backend=backend)
        with pytest.raises(FileNotFoundError, match="File not found"):
            inferencer.infer("nonexistent_file.pdf")

    def test_lexical_backend_no_file_check(self) -> None:
        inferencer = AutoInferencer(backend="lexical")
        ft = inferencer.infer("nonexistent_file.pdf")
        assert ".pdf" in ft.extensions

    @pytest.mark.parametrize("backend", ["magic", "magika", "hybrid"])
    def test_directory_raises_value_error(self, backend: str, temp_dir_path) -> None:
        inferencer = AutoInferencer(backend=backend)
        with pytest.raises(ValueError, match="Path is not a file"):
            inferencer.infer(str(temp_dir_path))

    def test_lexical_backend_directory_raises_value_error(self, temp_dir_path) -> None:
        inferencer = AutoInferencer(backend="lexical")
        with pytest.raises(ValueError, match="No extension found"):
            inferencer.infer(str(temp_dir_path))

    def test_invalid_backend_raises_keyerror(self) -> None:
        with pytest.raises(KeyError):
            AutoInferencer(backend="invalid")


class TestInputFlexibility:
    """AutoInferencer accepts both string and Path inputs."""

    def test_string_and_path_inputs(self, sample_pdf) -> None:
        inferencer = AutoInferencer(backend="magic")
        ft_str = inferencer.infer(str(sample_pdf))
        ft_path = inferencer.infer(sample_pdf)
        assert ft_str.extensions == ft_path.extensions
        assert ft_str.mime_types == ft_path.mime_types
