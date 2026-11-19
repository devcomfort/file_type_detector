"""Provides inferencer implementation that infers extensions from path strings only."""

from pathlib import Path

from ..core import BaseInferencer, FileType


class LexicalInferencer(BaseInferencer):
    """Inferencer that returns extensions by examining file path only.

    This strategy extracts the file extension directly from the path string
    without reading file contents. It is the fastest inference method but
    cannot detect or correct wrong extensions.

    Notes
    -----
    Does not read file content, so it's the fastest but cannot correct incorrect
    extensions.

    Examples
    --------
    >>> inferencer = LexicalInferencer()
    >>> ft = inferencer.detect("document.pdf")
    >>> '.pdf' in ft.extensions
    True
    """

    def detect(self, file_path: Path | str) -> FileType:
        """Extract extension from file path and return FileType.

        Parameters
        ----------
        file_path : Union[Path, str]
            The file path from which to read the extension.

        Returns
        -------
        FileType
            FileType instance containing the extension and corresponding MIME type.

        Raises
        ------
        ValueError
            Raised when the file path has no extension.

        Examples
        --------
        >>> inferencer = LexicalInferencer()
        >>> ft = inferencer.detect('document.pdf')
        >>> ft.extensions
        ('.pdf',)
        """
        ext = Path(file_path).suffix.lower()
        if not ext:
            raise ValueError(f"No extension found in file path: {file_path!r}")
        return FileType.from_extension(ext)
