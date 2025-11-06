"""Tests for LexicalInferencer."""

import pytest
from pathlib import Path
from loguru import logger

from filetype_detector.lexical_inferencer import LexicalInferencer


class TestLexicalInferencer:
    """Test suite for LexicalInferencer."""

    def test_infer_with_string_path(self):
        """Test inferring extension from string path."""
        logger.debug("Testing string path inference")
        inferencer = LexicalInferencer()
        result1 = inferencer.infer("document.pdf")
        result2 = inferencer.infer("data.txt")
        result3 = inferencer.infer("script.py")
        logger.success(f"String path test - Results: {result1}, {result2}, {result3}")
        assert result1 == ".pdf"
        assert result2 == ".txt"
        assert result3 == ".py"

    def test_infer_with_path_object(self):
        """Test inferring extension from Path object."""
        logger.debug("Testing Path object inference")
        inferencer = LexicalInferencer()
        result1 = inferencer.infer(Path("document.pdf"))
        result2 = inferencer.infer(Path("data.txt"))
        logger.success(f"Path object test - Results: {result1}, {result2}")
        assert result1 == ".pdf"
        assert result2 == ".txt"

    def test_infer_no_extension(self):
        """Test inferring extension when file has no extension."""
        logger.debug("Testing files without extension")
        inferencer = LexicalInferencer()
        result1 = inferencer.infer("no_extension")
        result2 = inferencer.infer(Path("file_without_ext"))
        logger.info(f"No extension test - Results: '{result1}', '{result2}'")
        assert result1 == ""
        assert result2 == ""

    def test_infer_case_insensitive(self):
        """Test that extension is returned in lowercase."""
        logger.debug("Testing case-insensitive extension extraction")
        inferencer = LexicalInferencer()
        test_cases = [
            ("file.PDF", ".pdf"),
            ("document.TXT", ".txt"),
            ("SCRIPT.PY", ".py"),
        ]
        for input_path, expected in test_cases:
            result = inferencer.infer(input_path)
            logger.debug(f"Input: {input_path} -> Result: {result}, Expected: {expected}")
            assert result == expected
        logger.success("Case-insensitive test passed")

    def test_infer_multiple_dots(self):
        """Test inferring extension from filename with multiple dots."""
        logger.debug("Testing filenames with multiple dots")
        inferencer = LexicalInferencer()
        result1 = inferencer.infer("file.tar.gz")
        result2 = inferencer.infer("backup.2024.01.01.txt")
        logger.info(f"Multiple dots test - Results: {result1}, {result2}")
        assert result1 == ".gz"
        assert result2 == ".txt"

    def test_infer_with_path_separators(self):
        """Test inferring extension from path with directory separators."""
        logger.debug("Testing paths with directory separators")
        inferencer = LexicalInferencer()
        result1 = inferencer.infer("path/to/file.pdf")
        result2 = inferencer.infer(Path("path/to/file.txt"))
        logger.success(f"Path separators test - Results: {result1}, {result2}")
        assert result1 == ".pdf"
        assert result2 == ".txt"

    def test_infer_empty_string(self):
        """Test inferring extension from empty string."""
        logger.warning("Testing empty string input")
        inferencer = LexicalInferencer()
        result1 = inferencer.infer("")
        result2 = inferencer.infer(Path(""))
        logger.info(f"Empty string test - Results: '{result1}', '{result2}'")
        assert result1 == ""
        assert result2 == ""

    def test_infer_dot_only(self):
        """Test inferring extension when filename starts with dot."""
        logger.debug("Testing filenames starting with dot")
        inferencer = LexicalInferencer()
        result1 = inferencer.infer(".hidden")
        result2 = inferencer.infer(".gitignore")
        logger.info(f"Dot-only test - Results: '{result1}', '{result2}'")
        assert result1 == ""
        assert result2 == ""

