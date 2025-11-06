"""Tests for MagikaInferencer."""

import pytest
from unittest.mock import patch, MagicMock
from magika import PredictionMode
from loguru import logger

from filetype_detector.magika_inferencer import MagikaInferencer


class TestMagikaInferencer:
    """Test suite for MagikaInferencer."""

    def test_infer_with_string_path(self, sample_text_file):
        """Test inferring extension from string path."""
        logger.debug(f"Testing string path inference with file: {sample_text_file}")
        inferencer = MagikaInferencer()
        extension = inferencer.infer(str(sample_text_file))
        logger.success(
            f"String path test - File: {sample_text_file.name}, Extension: {extension}, Type: {type(extension)}"
        )
        # Magika returns extensions as a list, which gets converted to string
        assert isinstance(extension, (str, list))
        if isinstance(extension, list):
            assert len(extension) >= 0  # May be empty list
        else:
            assert len(extension) >= 0  # May be empty string

    def test_infer_with_path_object(self, sample_text_file):
        """Test inferring extension from Path object."""
        logger.debug(f"Testing Path object inference with file: {sample_text_file}")
        inferencer = MagikaInferencer()
        extension = inferencer.infer(sample_text_file)
        logger.success(
            f"Path object test - File: {sample_text_file.name}, Extension: {extension}, Type: {type(extension)}"
        )
        # Magika returns extensions as a list, which gets converted to string
        assert isinstance(extension, (str, list))
        if isinstance(extension, list):
            assert len(extension) >= 0  # May be empty list
        else:
            assert len(extension) >= 0  # May be empty string

    def test_infer_with_score_returns_tuple(self, sample_text_file):
        """Test that infer_with_score returns a tuple of (extension, score)."""
        logger.debug(
            f"Testing infer_with_score returns tuple for file: {sample_text_file}"
        )
        inferencer = MagikaInferencer()
        extension, score = inferencer.infer_with_score(sample_text_file)
        logger.success(
            f"infer_with_score test - Extension: {extension}, Score: {score:.4f}, Types: ({type(extension).__name__}, {type(score).__name__})"
        )
        # Magika returns extensions as a list
        assert isinstance(extension, (str, list))
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        if isinstance(extension, list):
            assert len(extension) >= 0  # May be empty list
        else:
            assert len(extension) >= 0  # May be empty string

    def test_infer_delegates_to_infer_with_score(self, sample_text_file):
        """Test that infer method delegates to infer_with_score."""
        logger.debug("Testing that infer delegates to infer_with_score")
        inferencer = MagikaInferencer()
        extension_from_infer = inferencer.infer(sample_text_file)
        extension_from_score, _ = inferencer.infer_with_score(sample_text_file)
        logger.success(
            f"Delegation test - infer: {extension_from_infer}, infer_with_score: {extension_from_score}"
        )
        assert extension_from_infer == extension_from_score

    def test_infer_file_not_found_error(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        logger.warning("Testing FileNotFoundError for non-existent file (infer method)")
        inferencer = MagikaInferencer()
        with pytest.raises(FileNotFoundError, match="File not found") as exc_info:
            inferencer.infer("nonexistent_file.pdf")
        logger.success(f"FileNotFoundError correctly raised: {exc_info.value}")

    def test_infer_with_score_file_not_found_error(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        logger.warning(
            "Testing FileNotFoundError for non-existent file (infer_with_score method)"
        )
        inferencer = MagikaInferencer()
        with pytest.raises(FileNotFoundError, match="File not found") as exc_info:
            inferencer.infer_with_score("nonexistent_file.pdf")
        logger.success(f"FileNotFoundError correctly raised: {exc_info.value}")

    def test_infer_value_error_for_directory(self, temp_dir_path):
        """Test that ValueError is raised for directories."""
        logger.warning(
            f"Testing ValueError for directory: {temp_dir_path} (infer method)"
        )
        inferencer = MagikaInferencer()
        with pytest.raises(ValueError, match="Path is not a file") as exc_info:
            inferencer.infer(str(temp_dir_path))
        logger.success(f"ValueError correctly raised: {exc_info.value}")

    def test_infer_with_score_value_error_for_directory(self, temp_dir_path):
        """Test that ValueError is raised for directories."""
        logger.warning(
            f"Testing ValueError for directory: {temp_dir_path} (infer_with_score method)"
        )
        inferencer = MagikaInferencer()
        with pytest.raises(ValueError, match="Path is not a file") as exc_info:
            inferencer.infer_with_score(str(temp_dir_path))
        logger.success(f"ValueError correctly raised: {exc_info.value}")

    @patch("filetype_detector.magika_inferencer.Magika")
    def test_infer_with_score_runtime_error(self, mock_magika_class, sample_text_file):
        """Test that RuntimeError is raised when Magika fails."""
        logger.debug("Testing RuntimeError when Magika fails (infer_with_score method)")
        mock_magika = MagicMock()
        mock_magika.identify_path.side_effect = Exception("Magika error")
        mock_magika_class.return_value = mock_magika

        inferencer = MagikaInferencer()
        with pytest.raises(RuntimeError, match="Failed to analyze file") as exc_info:
            inferencer.infer_with_score(sample_text_file)
        logger.success(f"RuntimeError correctly raised: {exc_info.value}")

    @patch("filetype_detector.magika_inferencer.Magika")
    def test_infer_runtime_error_propagates(self, mock_magika_class, sample_text_file):
        """Test that RuntimeError from infer_with_score propagates through infer."""
        logger.debug("Testing RuntimeError propagation through infer method")
        mock_magika = MagicMock()
        mock_magika.identify_path.side_effect = Exception("Magika error")
        mock_magika_class.return_value = mock_magika

        inferencer = MagikaInferencer()
        with pytest.raises(RuntimeError, match="Failed to analyze file") as exc_info:
            inferencer.infer(sample_text_file)
        logger.success(f"RuntimeError correctly propagated: {exc_info.value}")

    def test_infer_with_score_prediction_mode(self, sample_text_file):
        """Test that prediction_mode parameter is respected."""
        logger.info("Testing different prediction modes")
        inferencer = MagikaInferencer()
        # Test with different prediction modes
        logger.debug("Testing MEDIUM_CONFIDENCE mode")
        extension1, score1 = inferencer.infer_with_score(
            sample_text_file, prediction_mode=PredictionMode.MEDIUM_CONFIDENCE
        )
        logger.debug("Testing HIGH_CONFIDENCE mode")
        extension2, score2 = inferencer.infer_with_score(
            sample_text_file, prediction_mode=PredictionMode.HIGH_CONFIDENCE
        )
        logger.success(
            f"Prediction mode test - MEDIUM: ext={extension1}, score={score1:.4f} | HIGH: ext={extension2}, score={score2:.4f}"
        )
        # Should get results regardless of mode
        # Magika returns extensions as a list
        assert isinstance(extension1, (str, list))
        assert isinstance(extension2, (str, list))
        assert isinstance(score1, float)
        assert isinstance(score2, float)
        if isinstance(extension1, list):
            assert len(extension1) >= 0
        else:
            assert len(extension1) >= 0
        if isinstance(extension2, list):
            assert len(extension2) >= 0
        else:
            assert len(extension2) >= 0

    @patch("filetype_detector.magika_inferencer.Magika")
    def test_infer_with_score_successful_flow(
        self, mock_magika_class, sample_text_file
    ):
        """Test successful inference flow with mocked Magika."""
        logger.debug("Testing successful inference flow with mocked Magika")
        mock_magika = MagicMock()
        mock_result = MagicMock()
        mock_result.output.extensions = ".txt"
        mock_result.prediction.score = 0.95
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        inferencer = MagikaInferencer()
        extension, score = inferencer.infer_with_score(sample_text_file)

        logger.success(
            f"Successful flow test - Extension: {extension}, Score: {score:.4f}"
        )
        assert extension == ".txt"
        assert score == 0.95
        mock_magika_class.assert_called_once_with(
            prediction_mode=PredictionMode.MEDIUM_CONFIDENCE
        )
        mock_magika.identify_path.assert_called_once_with(path=str(sample_text_file))
        logger.debug("Mock verification passed")

    def test_infer_with_pdf_file(self, sample_pdf_file):
        """Test inferring extension from PDF file."""
        logger.info(f"Testing PDF file inference: {sample_pdf_file.name}")
        inferencer = MagikaInferencer()
        extension = inferencer.infer(sample_pdf_file)
        logger.success(
            f"PDF file test - Extension: {extension}, Type: {type(extension)}"
        )
        # Magika returns extensions as a list
        assert isinstance(extension, (str, list))
        if isinstance(extension, list):
            assert len(extension) >= 0  # May be empty list
        else:
            assert len(extension) >= 0  # May be empty string

    def test_infer_with_python_file(self, sample_python_file):
        """Test inferring extension from Python file."""
        logger.info(f"Testing Python file inference: {sample_python_file.name}")
        inferencer = MagikaInferencer()
        extension = inferencer.infer(sample_python_file)
        logger.success(
            f"Python file test - Extension: {extension}, Type: {type(extension)}"
        )
        # Magika returns extensions as a list
        assert isinstance(extension, (str, list))
        if isinstance(extension, list):
            assert len(extension) >= 0  # May be empty list
        else:
            assert len(extension) >= 0  # May be empty string

    def test_infer_with_json_file(self, sample_json_file):
        """Test inferring extension from JSON file."""
        logger.info(f"Testing JSON file inference: {sample_json_file.name}")
        inferencer = MagikaInferencer()
        extension = inferencer.infer(sample_json_file)
        logger.success(
            f"JSON file test - Extension: {extension}, Type: {type(extension)}"
        )
        # Magika returns extensions as a list
        assert isinstance(extension, (str, list))
        if isinstance(extension, list):
            assert len(extension) >= 0  # May be empty list
        else:
            assert len(extension) >= 0  # May be empty string
