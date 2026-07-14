"""Provides Magika-based inferencer implementation."""

from ..core import BaseInferencer, FileType
from typing import Union, Tuple
from pathlib import Path
import mimetypes
from magika import Magika, PredictionMode


class MagikaInferencer(BaseInferencer):
    """Infers file type using Magika model.

    Inputs file content into a deep learning model to predict file type along
    with a confidence score. Based on learned features rather than fixed rules,
    so it excels at distinguishing detailed types of text-based files.

    Notes
    -----
    Inputs file content into a deep learning model to predict file type along with
    confidence score. Based on learned features rather than fixed rules, so it excels
    at distinguishing detailed types of text-based files.
    ``infer`` returns a :class:`FileType`, while ``infer_with_score`` returns an
    extension and confidence score.

    Examples
    --------
    >>> inferencer = MagikaInferencer()
    >>> ft = inferencer.infer('script.py')
    >>> '.py' in ft.extensions
    True
    """

    def __init__(
        self,
        prediction_mode: PredictionMode = PredictionMode.MEDIUM_CONFIDENCE,
    ) -> None:
        """Initialize MagikaInferencer.

        Parameters
        ----------
        prediction_mode : PredictionMode, optional
            Magika's prediction mode controlling the confidence threshold.
            Defaults to ``PredictionMode.MEDIUM_CONFIDENCE``.
        """
        self._prediction_mode = prediction_mode
        self._magika: Magika | None = None

    def _get_magika(self) -> Magika:
        """Lazily initialize Magika instance to avoid model load cost on construction.

        Returns
        -------
        Magika
            Initialized Magika instance.
        """
        if self._magika is None:
            self._magika = Magika(prediction_mode=self._prediction_mode)
        return self._magika

    def infer_with_score(
        self,
        file_path: Union[Path, str],
        prediction_mode: PredictionMode | None = None,
    ) -> Tuple[str, float]:
        """Return extension and confidence score together.

        Parameters
        ----------
        file_path : Union[Path, str]
            The file path to analyze.
        prediction_mode : PredictionMode, optional
            Override the default prediction mode for this call only.

        Returns
        -------
        Tuple[str, float]
            Inferred extension and confidence score (0.0 to 1.0).

        Raises
        ------
        FileNotFoundError
            Raised when the file does not exist.
        ValueError
            Raised when the path is not a file.
        RuntimeError
            Raised when Magika analysis fails.

        Examples
        --------
        >>> inferencer = MagikaInferencer()
        >>> extension, score = inferencer.infer_with_score('document.pdf')
        >>> print(extension, score)
        .pdf 0.99
        """
        path_obj = self._validate_path(file_path)

        magika = self._get_magika()
        mode = prediction_mode if prediction_mode is not None else self._prediction_mode
        if mode != self._prediction_mode:
            magika = Magika(prediction_mode=mode)

        try:
            result = magika.identify_path(path=str(path_obj))
            extensions = result.output.extensions
            extension = extensions[0] if extensions else ""
            score = result.prediction.score
            return (extension, score)
        except Exception as e:
            raise RuntimeError(f"Failed to analyze file {path_obj}: {str(e)}") from e

    def infer(self, file_path: Union[Path, str]) -> FileType:
        """Infer file type using Magika model and return FileType.

        Parameters
        ----------
        file_path : Union[Path, str]
            The file path to analyze.

        Returns
        -------
        FileType
            FileType instance containing inferred extensions and MIME type.

        Raises
        ------
        FileNotFoundError
            Raised when the file does not exist.
        ValueError
            Raised when the path is not a file.
        RuntimeError
            Raised when Magika analysis fails.

        Examples
        --------
        >>> inferencer = MagikaInferencer()
        >>> ft = inferencer.infer('document.pdf')
        >>> '.pdf' in ft.extensions
        True
        """
        path_obj = self._validate_path(file_path)
        magika = self._get_magika()

        try:
            result = magika.identify_path(path=str(path_obj))
            extensions = result.output.extensions

            normalized_exts = [FileType.normalize_extension(ext) for ext in extensions]

            mime, _ = (
                mimetypes.guess_type(f"file{normalized_exts[0]}", strict=False)
                if normalized_exts
                else (None, None)
            )
            mime_types = (mime,) if mime else ()

            return FileType(extensions=tuple(normalized_exts), mime_types=mime_types)
        except Exception as e:
            raise RuntimeError(f"Failed to analyze file {path_obj}: {str(e)}") from e
