"""Provides a hybrid inferencer combining Magic and Magika.

This module's implementation first applies Magic to all files, and additionally
uses Magika for files identified with ambiguous MIME types (text/*, text/plain,
text/x-c, application/octet-stream). This design reduces processing cost for
files with specific MIME types while achieving finer classification for files
where Magic produces generic results.
"""

from ..core import BaseInferencer, FileType
from typing import Union
from pathlib import Path
import magic
from magika import Magika, PredictionMode

MAGIKA_CONFIDENCE_THRESHOLD = 0.5
"""Minimum Magika confidence score to accept its result over Magic's."""

# MIME types from libmagic that are generic/non-specific and should be refined by Magika
AMBIGUOUS_MIME_TYPES = frozenset({
    "text/plain",
    "text/x-c",
    "application/octet-stream",
})


class HybridInferencer(BaseInferencer):
    """Inferencer that combines Magic and Magika strategies sequentially.

    First determines MIME type with Magic, then re-analyzes files with
    ambiguous Magic results using Magika. Files with specific MIME types
    use Magic results directly, making this strategy fast for well-known
    formats and precise for files where Magic produces generic results.

    Notes
    -----
    Magika is invoked when Magic returns a MIME type starting with ``text/``
    or in :data:`AMBIGUOUS_MIME_TYPES` (``text/plain``, ``text/x-c``,
    ``application/octet-stream``). Magika's MIME type and extensions are
    preserved directly, avoiding lossy re-derivation through ``mimetypes``.

    Examples
    --------
    >>> inferencer = HybridInferencer()
    >>> ft = inferencer.infer('document.pdf')
    >>> '.pdf' in ft.extensions
    True
    """

    def __init__(self) -> None:
        """Initialize HybridInferencer.

        Magika model is loaded lazily on first text file inference to avoid
        upfront cost when only binary files are processed.
        """
        self._magika: Magika | None = None

    def _get_magika(self) -> Magika:
        """Lazily initialize Magika instance to avoid model load cost on construction.

        Returns
        -------
        Magika
            Initialized Magika instance with medium confidence mode.
        """
        if self._magika is None:
            self._magika = Magika(prediction_mode=PredictionMode.MEDIUM_CONFIDENCE)
        return self._magika

    def infer(self, file_path: Union[Path, str]) -> FileType:
        """Infer file type using hybrid strategy.

        The strategy works as follows:

        1. Magic analyzes the file and returns a MIME type.
        2. If the MIME type starts with ``text/`` or is in
           :data:`AMBIGUOUS_MIME_TYPES`, Magika re-analyzes the file
           for finer classification.
        3. If Magika's confidence score is below
           :data:`MAGIKA_CONFIDENCE_THRESHOLD`, the Magic result is used.
        4. If Magika succeeds with sufficient confidence, Magika's MIME type
           and extensions are used directly.
        5. If Magika fails, a warning is issued and the Magic result is used.

        Parameters
        ----------
        file_path : Union[Path, str]
            The file path to analyze.

        Returns
        -------
        FileType
            FileType instance containing inferred extension and MIME type.
            For files with ambiguous Magic results, reflects Magika refinement.

        Raises
        ------
        FileNotFoundError
            Raised when the file does not exist.
        ValueError
            Raised when the path is not a file.
        RuntimeError
            Raised when MIME type cannot be determined.

        Examples
        --------
        >>> inferencer = HybridInferencer()
        >>> ft = inferencer.infer('document.pdf')
        >>> '.pdf' in ft.extensions
        True
        """
        path_obj = self._validate_path(file_path)

        mime_type = magic.from_file(str(path_obj), mime=True)
        if mime_type is None:
            raise RuntimeError(f"Cannot determine MIME type for file: {path_obj}")

        if mime_type.startswith("text/") or mime_type in AMBIGUOUS_MIME_TYPES:
            try:
                magika = self._get_magika()
                result = magika.identify_path(path=str(path_obj))

                extensions = result.output.extensions
                score = result.prediction.score

                if score < MAGIKA_CONFIDENCE_THRESHOLD:
                    return FileType.from_mimetype(mime_type)

                if isinstance(extensions, list) and len(extensions) > 0:
                    normalized_exts = [
                        FileType.normalize_extension(ext) for ext in extensions
                    ]
                    magika_mime = getattr(result.output, "mime_type", None)
                    if isinstance(magika_mime, str) and magika_mime:
                        return FileType(
                            extensions=tuple(normalized_exts),
                            mime_types=(magika_mime,),
                        )
                    else:
                        extension = FileType.normalize_extension(extensions[0])
                        return FileType.from_extension(extension)
                elif isinstance(extensions, str) and extensions:
                    normalized_exts = [FileType.normalize_extension(extensions)]
                    magika_mime = getattr(result.output, "mime_type", None)
                    if isinstance(magika_mime, str) and magika_mime:
                        return FileType(
                            extensions=tuple(normalized_exts),
                            mime_types=(magika_mime,),
                        )
                    else:
                        extension = FileType.normalize_extension(extensions)
                        return FileType.from_extension(extension)
            except Exception as e:
                import warnings

                warnings.warn(
                    f"Magika fallback to Magic for {path_obj}: {e}",
                    RuntimeWarning,
                    stacklevel=2,
                )

        return FileType.from_mimetype(mime_type)
