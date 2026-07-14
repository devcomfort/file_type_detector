"""Behavior and control-flow tests for HybridInferencer.

Semantic accuracy tests that assert specific MIME types/extensions for real
fixtures live in ``tests/test_accuracy_hybrid.py``. This file covers only the
inferencer's internal control flow, error handling, and gate logic via mocks.
"""

import pytest
from unittest.mock import patch, MagicMock

from filetype_detector.strategies import HybridInferencer


class TestHybridInferencer:
    @pytest.mark.parametrize("input_type", ["str", "path"])
    def test_infer_with_string_and_path(self, input_type, sample_text_file):
        target = str(sample_text_file) if input_type == "str" else sample_text_file
        ft = HybridInferencer().infer(target)
        assert len(ft.extensions) > 0
        assert all(ext.startswith(".") for ext in ft.extensions)

    def test_file_not_found_error(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            HybridInferencer().infer("nonexistent_file.pdf")

    def test_value_error_for_directory(self, temp_dir_path):
        with pytest.raises(ValueError, match="Path is not a file"):
            HybridInferencer().infer(str(temp_dir_path))

    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_runtime_error_no_mime_type(self, mock_magic, sample_text_file):
        mock_magic.return_value = None
        with pytest.raises(RuntimeError, match="Cannot determine MIME type"):
            HybridInferencer().infer(sample_text_file)

    @pytest.mark.parametrize(
        "fixture_name",
        ["sample_text_file", "sample_python_file", "sample_json_file"],
    )
    def test_text_files_detected(self, fixture_name, request):
        sample_file = request.getfixturevalue(fixture_name)
        ft = HybridInferencer().infer(sample_file)
        assert len(ft.extensions) > 0

    def test_pdf_file_uses_magic_only(self, sample_pdf_file):
        ft = HybridInferencer().infer(sample_pdf_file)
        assert ".pdf" in ft.extensions

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_text_file_cascades_to_magika(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        mock_magic.return_value = "text/plain"
        mock_result = MagicMock()
        mock_result.output.extensions = ["txt"]
        mock_result.prediction.score = 0.95
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        mock_magic.assert_called_once()
        mock_magika_class.assert_called_once()
        assert ".txt" in ft.extensions

    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_specific_mime_skips_magika(self, mock_magic, sample_pdf_file):
        """Non-ambiguous MIME (not in AMBIGUOUS_MIME_TYPES, not text/) skips Magika."""
        mock_magic.return_value = "application/pdf"
        ft = HybridInferencer().infer(sample_pdf_file)
        mock_magic.assert_called_once()
        assert ".pdf" in ft.extensions

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_magika_failure_falls_back_to_magic(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        mock_magic.return_value = "text/plain"
        mock_magika = MagicMock()
        mock_magika.identify_path.side_effect = Exception("Magika error")
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        assert ".txt" in ft.extensions
        mock_magic.assert_called_once()
        mock_magika.identify_path.assert_called_once()

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_magika_empty_result_falls_back_to_magic(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        mock_magic.return_value = "text/plain"
        mock_result = MagicMock()
        mock_result.output.extensions = []
        mock_result.prediction.score = 0.95
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        assert ".txt" in ft.extensions

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_magika_extension_without_dot(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        mock_magic.return_value = "text/plain"
        mock_result = MagicMock()
        mock_result.output.extensions = ["py"]
        mock_result.prediction.score = 0.95
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        assert ".py" in ft.extensions

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_magika_extension_as_string(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        mock_magic.return_value = "text/plain"
        mock_result = MagicMock()
        mock_result.output.extensions = "json"
        mock_result.prediction.score = 0.95
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        assert ".json" in ft.extensions

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_magika_low_confidence_falls_back_to_magic(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        mock_magic.return_value = "text/plain"
        mock_result = MagicMock()
        mock_result.output.extensions = ["txt"]
        mock_result.prediction.score = 0.3
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        assert ".txt" in ft.extensions
        assert "text/plain" in ft.mime_types

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_octet_stream_triggers_magika(
        self, mock_magic, mock_magika_class, sample_pdf_file
    ):
        """Post-Task5: application/octet-stream opens the Magika gate."""
        mock_magic.return_value = "application/octet-stream"
        mock_result = MagicMock()
        mock_result.output.extensions = ["wasm"]
        mock_result.output.mime_type = "application/wasm"
        mock_result.prediction.score = 0.99
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_pdf_file)

        mock_magic.assert_called_once()
        mock_magika.identify_path.assert_called_once()
        assert "application/wasm" in ft.mime_types

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_text_x_c_triggers_magika(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        """Post-Task5: text/x-c opens the Magika gate."""
        mock_magic.return_value = "text/x-c"
        mock_result = MagicMock()
        mock_result.output.extensions = ["js"]
        mock_result.output.mime_type = "application/javascript"
        mock_result.prediction.score = 0.99
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        mock_magic.assert_called_once()
        mock_magika.identify_path.assert_called_once()
        assert "application/javascript" in ft.mime_types

    @patch("filetype_detector.strategies.hybrid_inferencer.Magika")
    @patch("filetype_detector.strategies.hybrid_inferencer.magic.from_file")
    def test_magika_mime_preserved_in_hybrid_result(
        self, mock_magic, mock_magika_class, sample_text_file
    ):
        """Post-Task5: Magika's result.output.mime_type is used directly."""
        mock_magic.return_value = "text/plain"
        mock_result = MagicMock()
        mock_result.output.extensions = ["rs"]
        mock_result.output.mime_type = "application/x-rust"
        mock_result.prediction.score = 0.95
        mock_magika = MagicMock()
        mock_magika.identify_path.return_value = mock_result
        mock_magika_class.return_value = mock_magika

        ft = HybridInferencer().infer(sample_text_file)

        assert "application/x-rust" in ft.mime_types
