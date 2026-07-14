"""Tests for LexicalInferencer."""

import pytest
from pathlib import Path

from filetype_detector.strategies import LexicalInferencer


class TestLexicalInferencer:
    @pytest.mark.parametrize(
        "filename, expected_ext",
        [
            ("document.pdf", ".pdf"),
            ("data.txt", ".txt"),
            ("script.py", ".py"),
        ],
    )
    def test_infer_with_string_path(self, filename, expected_ext):
        result = LexicalInferencer().infer(filename)
        assert expected_ext in result.extensions

    @pytest.mark.parametrize(
        "filename, expected_ext",
        [
            ("document.pdf", ".pdf"),
            ("data.txt", ".txt"),
        ],
    )
    def test_infer_with_path_object(self, filename, expected_ext):
        result = LexicalInferencer().infer(Path(filename))
        assert expected_ext in result.extensions

    @pytest.mark.parametrize("filename", ["no_extension", "file_without_ext"])
    def test_infer_no_extension(self, filename):
        with pytest.raises(ValueError, match="No extension found"):
            LexicalInferencer().infer(filename)

    @pytest.mark.parametrize(
        "filename, expected_ext",
        [
            ("file.PDF", ".pdf"),
            ("document.TXT", ".txt"),
            ("SCRIPT.PY", ".py"),
        ],
    )
    def test_infer_case_insensitive(self, filename, expected_ext):
        result = LexicalInferencer().infer(filename)
        assert expected_ext in result.extensions

    @pytest.mark.parametrize(
        "filename, expected_ext",
        [
            ("file.tar.gz", ".gz"),
            ("backup.2024.01.01.txt", ".txt"),
        ],
    )
    def test_infer_multiple_dots(self, filename, expected_ext):
        result = LexicalInferencer().infer(filename)
        assert expected_ext in result.extensions

    @pytest.mark.parametrize(
        "path",
        [
            "path/to/file.pdf",
            Path("path/to/file.txt"),
        ],
    )
    def test_infer_with_path_separators(self, path):
        result = LexicalInferencer().infer(path)
        assert result.extensions[0] in (".pdf", ".txt")

    @pytest.mark.parametrize("filename", ["", Path("")])
    def test_infer_empty_string(self, filename):
        with pytest.raises(ValueError, match="No extension found"):
            LexicalInferencer().infer(filename)

    @pytest.mark.parametrize("filename", [".hidden", ".gitignore"])
    def test_infer_dot_only(self, filename):
        with pytest.raises(ValueError, match="No extension found"):
            LexicalInferencer().infer(filename)
