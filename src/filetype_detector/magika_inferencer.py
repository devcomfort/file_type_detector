from .base_inferencer import BaseInferencer
from typing import Union, Tuple
from pathlib import Path
from magika import Magika, PredictionMode


class MagikaInferencer(BaseInferencer):
    """Magika inferencer that uses Google's Magika AI to infer file format.

    The class provides a public `infer` method that returns only the file
    extension, while the heavy‑lifting is performed by the `infer_with_score`
    method which returns both extension and confidence score.

    Attributes
    ----------
    None
    """

    def infer_with_score(
        self,
        file_path: Union[Path, str],
        prediction_mode: PredictionMode = PredictionMode.MEDIUM_CONFIDENCE,
    ) -> Tuple[str, float]:
        """Core implementation that returns both extension and confidence score.

        Parameters
        ----------
        file_path : Union[Path, str]
            Path to the file to analyze. Can be a string or `Path` object.
        prediction_mode : PredictionMode, optional
            Magika prediction mode controlling confidence level. Defaults to
            `PredictionMode.MEDIUM_CONFIDENCE`.

        Returns
        -------
        Tuple[str, float]
            Tuple of `(extension, confidence_score)` where `extension` includes
            the leading dot (e.g., `'.pdf'`) and `confidence_score` is a float
            between 0.0 and 1.0.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the path is not a file.
        RuntimeError
            If Magika fails to analyze the file.

        Examples
        --------
        >>> inferencer = MagikaInferencer()
        >>> extension, score = inferencer.infer_with_score('document.pdf')
        >>> print(extension, score)
        .pdf 0.99
        >>> extension, score = inferencer.infer_with_score(Path('notes.txt'))
        >>> print(extension, score)
        .txt 0.97
        """
        # Convert to string for Magika compatibility
        file_path_str = str(file_path)

        # Validate file exists and is accessible
        path_obj = Path(file_path_str)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path_str}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {file_path_str}")

        magika = Magika(prediction_mode=prediction_mode)

        # Perform content type detection
        try:
            result = magika.identify_path(path=file_path_str)
            extension = result.output.extensions
            score = result.prediction.score
            return (extension, score)
        except Exception as e:
            raise RuntimeError(
                f"Failed to analyze file {file_path_str}: {str(e)}"
            ) from e

    def infer(self, file_path: Union[Path, str]) -> str:
        """Public API that returns only the file extension.

        This method delegates to `infer_with_score` and discards the
        confidence score, returning just the extension.

        Parameters
        ----------
        file_path : Union[Path, str]
            Path to the file to analyze. Can be a string or `Path` object.

        Returns
        -------
        str
            File extension with leading dot (e.g., `'.pdf'`, `'.txt'`).
            The exact format depends on Magika's output format.

        Examples
        --------
        >>> inferencer = MagikaInferencer()
        >>> inferencer.infer('document.pdf')
        '.pdf'
        >>> inferencer.infer(Path('notes.txt'))
        '.txt'

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the path is not a file.
        RuntimeError
            If Magika fails to analyze the file.
        """
        extension, _ = self.infer_with_score(
            file_path, prediction_mode=PredictionMode.MEDIUM_CONFIDENCE
        )
        return extension
