"""Provides libmagic-based inferencer implementation."""

from ..core import BaseInferencer, FileType
from typing import Union
from pathlib import Path
import magic


class MagicInferencer(BaseInferencer):
    """Infers file type using python-magic.

    Compares magic bytes and byte patterns in the file with the libmagic
    database to determine MIME type, then converts to extensions using
    Python's :mod:`mimetypes` module.

    This strategy does not depend on filename or extension, making it useful
    for files without extensions or with incorrect extensions.

    Notes
    -----
    Compares magic bytes and byte patterns in the file with the libmagic database
    to determine MIME type, then converts to extensions using `mimetypes`.
    Does not depend on filename or extension, so it's useful for files without
    or with incorrect extensions.

    Examples
    --------
    >>> inferencer = MagicInferencer()
    >>> ft = inferencer.infer('document.pdf')
    >>> '.pdf' in ft.extensions
    True
    """

    def infer(self, file_path: Union[Path, str]) -> FileType:
        """Infer FileType from file content.

        Parameters
        ----------
        file_path : Union[Path, str]
            The file path to analyze.

        Returns
        -------
        FileType
            FileType instance containing extensions inferred from MIME type.

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
        >>> inferencer = MagicInferencer()
        >>> ft = inferencer.infer('document.pdf')
        >>> '.pdf' in ft.extensions
        True
        """
        path_obj = self._validate_path(file_path)

        mime_type = magic.from_file(str(path_obj), mime=True)
        if mime_type is None:
            raise RuntimeError(f"Cannot determine MIME type for file: {path_obj}")

        return FileType.from_mimetype(mime_type)
