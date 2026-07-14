"""Module that wraps multiple inferencers under a single interface.

`AutoInferencer` accepts a string backend key and selects the appropriate
inferencer implementation. Path-based inference, Magic-based inference, Magika-based
inference, and hybrid inference combining both methods can be used in the same way.
"""

from typing import Literal, Union
from pathlib import Path

from .core import BaseInferencer, FileType
from .strategies import (
    LexicalInferencer,
    MagicInferencer,
    MagikaInferencer,
    HybridInferencer,
)


BackendType = Literal["lexical", "magic", "magika", "hybrid"]
"""String literal type of public backend keys supported by :class:`AutoInferencer`."""

_BACKEND_MAP: dict[str, type[BaseInferencer]] = {
    "lexical": LexicalInferencer,
    "magic": MagicInferencer,
    "magika": MagikaInferencer,
    "hybrid": HybridInferencer,
}


class AutoInferencer(BaseInferencer):
    """Inferencer that delegates to the selected backend implementation.

    Parameters
    ----------
    backend : BackendType
        The name of the backend to use.

        - ``"lexical"``: Reads extension directly from the path.
        - ``"magic"``: Determines MIME type based on file content.
        - ``"magika"``: Analyzes content using Magika model.
        - ``"hybrid"``: Classifies with Magic first, then re-analyzes text files with Magika.

    Examples
    --------
    >>> result = AutoInferencer(backend="lexical").infer("document.pdf")
    >>> result.extensions
    ('.pdf',)
    >>> result.mime_types
    ('application/pdf',)
    """

    def __init__(self, backend: BackendType = "hybrid") -> None:
        """Initialize AutoInferencer with the specified backend.

        Parameters
        ----------
        backend : BackendType
            The backend strategy to use. Defaults to ``"hybrid"``.
        """
        self._inferencer: BaseInferencer = _BACKEND_MAP[backend]()

    def infer(self, file_path: Union[Path, str]) -> FileType:
        """Infer file type using the configured backend.

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
            Raised when the backend fails to determine the file type.
        """
        return self._inferencer.infer(file_path)
