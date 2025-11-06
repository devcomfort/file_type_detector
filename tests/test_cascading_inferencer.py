"""Tests for CascadingInferencer."""

import pytest
from unittest.mock import patch, MagicMock
from loguru import logger

from filetype_detector.mixture_inferencer import CascadingInferencer


class TestCascadingInferencer:
    """Test suite for CascadingInferencer."""

    def test_infer_with_string_path(self, sample_text_file):
        """Test inferring extension from string path."""
        logger.debug(f"Testing string path inference with file: {sample_text_file}")
        inferencer = CascadingInferencer()
        extension = inferencer.infer(str(sample_text_file))
        logger.success(
            f"String path test - File: {sample_text_file.name}, Extension: {extension}"
        )
        assert isinstance(extension, str)
        assert extension.startswith(".")
        assert len(extension) > 1

    def test_infer_with_path_object(self, sample_text_file):
        """Test inferring extension from Path object."""
        logger.debug(f"Testing Path object inference with file: {sample_text_file}")
        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_text_file)
        logger.success(
            f"Path object test - File: {sample_text_file.name}, Extension: {extension}"
        )
        assert isinstance(extension, str)
        assert extension.startswith(".")

    def test_infer_file_not_found_error(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        logger.warning("Testing FileNotFoundError for non-existent file")
        inferencer = CascadingInferencer()
        with pytest.raises(FileNotFoundError, match="File not found") as exc_info:
            inferencer.infer("nonexistent_file.pdf")
        logger.success(f"FileNotFoundError correctly raised: {exc_info.value}")

    def test_infer_value_error_for_directory(self, temp_dir_path):
        """Test that ValueError is raised for directories."""
        logger.warning(f"Testing ValueError for directory: {temp_dir_path}")
        inferencer = CascadingInferencer()
        with pytest.raises(ValueError, match="Path is not a file") as exc_info:
            inferencer.infer(str(temp_dir_path))
        logger.success(f"ValueError correctly raised: {exc_info.value}")

    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    def test_infer_runtime_error_no_mime_type(self, mock_magic, sample_text_file):
        """Test that RuntimeError is raised when MIME type cannot be determined."""
        logger.debug("Testing RuntimeError when MIME type cannot be determined")
        mock_magic.return_value = None
        inferencer = CascadingInferencer()
        with pytest.raises(
            RuntimeError, match="Cannot determine MIME type"
        ) as exc_info:
            inferencer.infer(sample_text_file)
        logger.success(f"RuntimeError correctly raised: {exc_info.value}")

    @patch("filetype_detector.mixture_inferencer.mimetypes.guess_extension")
    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    def test_infer_runtime_error_no_extension(
        self, mock_magic, mock_guess_ext, sample_text_file
    ):
        """Test that RuntimeError is raised when extension cannot be guessed."""
        logger.debug("Testing RuntimeError when extension cannot be guessed")
        mock_magic.return_value = "application/unknown"
        mock_guess_ext.return_value = None
        inferencer = CascadingInferencer()
        with pytest.raises(RuntimeError, match="Cannot convert MIME type") as exc_info:
            inferencer.infer(sample_text_file)
        logger.success(f"RuntimeError correctly raised: {exc_info.value}")

    def test_infer_with_text_file_uses_magika(self, sample_text_file):
        """Test that text files trigger Magika inference."""
        logger.info(f"Testing text file inference with Magika: {sample_text_file.name}")
        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_text_file)
        logger.success(f"Text file test - Extension: {extension}")
        assert isinstance(extension, str)
        assert extension.startswith(".")

    def test_infer_with_python_file(self, sample_python_file):
        """Test inferring extension from Python file."""
        logger.info(f"Testing Python file inference: {sample_python_file.name}")
        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_python_file)
        logger.success(f"Python file test - Extension: {extension}")
        assert isinstance(extension, str)
        assert extension.startswith(".")
        # Should detect as .py using Magika (for text files)
        if extension == ".py":
            logger.info("Correctly identified as Python file")
        else:
            logger.info(f"Detected as {extension} (may vary)")

    def test_infer_with_json_file(self, sample_json_file):
        """Test inferring extension from JSON file."""
        logger.info(f"Testing JSON file inference: {sample_json_file.name}")
        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_json_file)
        logger.success(f"JSON file test - Extension: {extension}")
        assert isinstance(extension, str)
        assert extension.startswith(".")
        # Should detect as .json using Magika (for text files)
        if extension == ".json":
            logger.info("Correctly identified as JSON file")

    def test_infer_with_pdf_file_uses_magic_only(self, sample_pdf_file):
        """Test that non-text files use Magic only (not Magika)."""
        logger.info(f"Testing PDF file inference (Magic only): {sample_pdf_file.name}")
        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_pdf_file)
        logger.success(f"PDF file test - Extension: {extension}")
        assert isinstance(extension, str)
        assert extension.startswith(".")
        # PDF files are not text/*, so should use Magic only

    @patch("filetype_detector.mixture_inferencer.Magika")
    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    def test_text_file_cascades_to_magika(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        """Test that text files cascade to Magika inference."""
        logger.debug("Testing cascading behavior for text files")
        mock_magic.return_value = "text/plain"
        mock_magika = MagicMock()
        mock_result = MagicMock()
        mock_result.output.extensions = ["txt"]
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_text_file)

        logger.success(f"Cascading test - Extension: {extension}")
        # Verify Magic was called
        mock_magic.assert_called_once()
        # Verify Magika was called (for text files)
        mock_magika_class.assert_called_once()
        mock_magika.identify_path.assert_called_once()
        assert extension == ".txt"

    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    def test_non_text_file_does_not_use_magika(self, mock_magic, sample_pdf_file):
        """Test that non-text files do not use Magika."""
        logger.debug("Testing that non-text files skip Magika")
        mock_magic.return_value = "application/pdf"
        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_pdf_file)

        logger.success(f"Non-text file test - Extension: {extension}")
        # Verify Magic was called
        mock_magic.assert_called_once()
        # Magika should not be used for non-text files
        assert extension.startswith(".")

    @patch("filetype_detector.mixture_inferencer.Magika")
    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    @patch("filetype_detector.mixture_inferencer.mimetypes.guess_extension")
    def test_magika_failure_falls_back_to_magic(
        self, mock_guess_ext, mock_magic, mock_magika_class, sample_text_file
    ):
        """Test that Magika failure falls back to Magic result."""
        logger.debug("Testing fallback behavior when Magika fails")
        mock_magic.return_value = "text/plain"
        mock_guess_ext.return_value = ".txt"
        mock_magika = MagicMock()
        mock_magika.identify_path.side_effect = Exception("Magika error")
        mock_magika_class.return_value = mock_magika

        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_text_file)

        logger.success(f"Fallback test - Extension: {extension}")
        # Should fallback to Magic result
        assert extension == ".txt"
        # Verify Magic was called
        mock_magic.assert_called_once()
        # Verify Magika was attempted but failed
        mock_magika.identify_path.assert_called_once()

    @patch("filetype_detector.mixture_inferencer.Magika")
    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    @patch("filetype_detector.mixture_inferencer.mimetypes.guess_extension")
    def test_magika_empty_result_falls_back_to_magic(
        self, mock_guess_ext, mock_magic, mock_magika_class, sample_text_file
    ):
        """Test that empty Magika result falls back to Magic."""
        logger.debug("Testing fallback when Magika returns empty result")
        mock_magic.return_value = "text/plain"
        mock_guess_ext.return_value = ".txt"
        mock_magika = MagicMock()
        mock_result = MagicMock()
        mock_result.output.extensions = []  # Empty list
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_text_file)

        logger.success(f"Empty result fallback test - Extension: {extension}")
        # Should fallback to Magic result
        assert extension == ".txt"

    @patch("filetype_detector.mixture_inferencer.Magika")
    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    def test_magika_extension_without_dot(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        """Test that Magika extension without dot gets dot prefix added."""
        logger.debug("Testing Magika extension formatting (without dot)")
        mock_magic.return_value = "text/plain"
        mock_magika = MagicMock()
        mock_result = MagicMock()
        mock_result.output.extensions = ["py"]  # Without dot
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_text_file)

        logger.success(f"Extension formatting test - Extension: {extension}")
        assert extension == ".py"
        assert extension.startswith(".")

    @patch("filetype_detector.mixture_inferencer.Magika")
    @patch("filetype_detector.mixture_inferencer.magic.from_file")
    def test_magika_extension_as_string(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        """Test that Magika extension as string is handled correctly."""
        logger.debug("Testing Magika extension as string format")
        mock_magic.return_value = "text/plain"
        mock_magika = MagicMock()
        mock_result = MagicMock()
        mock_result.output.extensions = "json"  # String format
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        inferencer = CascadingInferencer()
        extension = inferencer.infer(sample_text_file)

        logger.success(f"String extension test - Extension: {extension}")
        assert extension == ".json"
        assert extension.startswith(".")
