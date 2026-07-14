"""Tests for MagikaInferencer edge cases and error handling.

Behavior and exception tests only. Semantic accuracy tests live in
``tests/test_accuracy_magika.py``.
"""

import pytest
from filetype_detector.strategies import MagikaInferencer
from filetype_detector.core import FileType


class TestMagikaInferencerEdgeCases:
    def test_infer_returns_filetype(self, sample_txt):
        ft = MagikaInferencer().infer(sample_txt)
        assert isinstance(ft, FileType)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            MagikaInferencer().infer("nonexistent_file.pdf")

    def test_directory_raises_value_error(self, temp_dir_path):
        with pytest.raises(ValueError, match="Path is not a file"):
            MagikaInferencer().infer(str(temp_dir_path))

    def test_infer_with_score_returns_tuple(self, sample_txt):
        extension, score = MagikaInferencer().infer_with_score(sample_txt)
        assert isinstance(extension, str)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0