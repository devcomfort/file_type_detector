"""Tests for MagicInferencer edge cases and exception handling.

Verifies error handling, path-acceptance behavior, and edge cases.
Semantic accuracy tests live in ``test_accuracy_magic.py``.
"""

import pytest
from filetype_detector.strategies import MagicInferencer


class TestMagicInferencerEdgeCases:
    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            MagicInferencer().infer("nonexistent_file.pdf")

    def test_directory_raises_value_error(self, temp_dir_path):
        with pytest.raises(ValueError, match="Path is not a file"):
            MagicInferencer().infer(str(temp_dir_path))

    def test_none_mime_raises_runtime_error(self, sample_pdf):
        from unittest.mock import patch
        with patch("filetype_detector.strategies.magic_inferencer.magic.from_file", return_value=None):
            with pytest.raises(RuntimeError, match="Cannot determine MIME type"):
                MagicInferencer().infer(sample_pdf)

    def test_accepts_string_path(self, sample_pdf):
        result = MagicInferencer().infer(str(sample_pdf))
        assert ".pdf" in result.extensions
        assert "application/pdf" in result.mime_types

    def test_accepts_path_object(self, sample_pdf):
        result = MagicInferencer().infer(sample_pdf)
        assert ".pdf" in result.extensions
