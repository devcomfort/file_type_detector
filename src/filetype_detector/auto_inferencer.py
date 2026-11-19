
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






    Parameters
    ----------

        - ``"lexical"``: Reads extension directly from the path.

    Examples
    --------
    >>> result.extensions
    ('.pdf',)
    >>> result.mime_types
    ('application/pdf',)
    """

    def __init__(self, backend: BackendType = "hybrid") -> None:

        Parameters
        ----------
        backend : BackendType
        """

    def infer(self, file_path: Union[Path, str]) -> FileType:

        Parameters
        ----------
        file_path : Union[Path, str]
            The file path to analyze.

        Returns
        -------
        FileType

        Raises
        ------
        FileNotFoundError
            Raised when the file does not exist.
        ValueError
        RuntimeError
            Raised when the backend fails to determine the file type.
        """
