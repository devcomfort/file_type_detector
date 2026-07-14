"""Data schema that stores file extensions and MIME types."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass


@dataclass(frozen=True)
class FileType:
    """Stores file extensions and MIME types.

    Parameters
    ----------
    extensions : tuple[str, ...]
        Tuple of file extensions (e.g., ``('.pdf',)``, ``('.jpg', '.jpeg')``).
    mime_types : tuple[str, ...]
        Tuple of MIME types (e.g., ``('application/pdf',)``, ``('image/jpeg',)``).

    Examples
    --------
    >>> ft = FileType(('.pdf',), ('application/pdf',))
    >>> ft.extensions
    ('.pdf',)
    >>> ft.mime_types
    ('application/pdf',)
    """

    extensions: tuple[str, ...] = ()
    mime_types: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return (
            f"FileType(extensions={self.extensions!r}, mime_types={self.mime_types!r})"
        )

    @staticmethod
    def normalize_extension(ext: str) -> str:
        """Ensure extension has a leading dot.

        Parameters
        ----------
        ext : str
            File extension, with or without leading dot (e.g., ``'pdf'`` or ``'.pdf'``).

        Returns
        -------
        str
            Extension with leading dot (e.g., ``'.pdf'``).

        Examples
        --------
        >>> FileType.normalize_extension('pdf')
        '.pdf'
        >>> FileType.normalize_extension('.pdf')
        '.pdf'
        """
        return ext if ext.startswith(".") else f".{ext}"

    @classmethod
    def from_extension(cls, ext: str) -> FileType:
        """Create FileType from extension.

        Parameters
        ----------
        ext : str
            File extension including dot (e.g., ``'.pdf'``, ``'.jpg'``).

        Returns
        -------
        FileType
            FileType instance containing the extension and corresponding MIME type.

        Examples
        --------
        >>> ft = FileType.from_extension('.pdf')
        >>> '.pdf' in ft.extensions
        True
        >>> 'application/pdf' in ft.mime_types
        True
        """
        mime, _ = mimetypes.guess_type(f"file{ext}", strict=False)
        mime_types_set = {mime} if mime else set()

        return cls(
            extensions=(ext,),
            mime_types=tuple(mime_types_set),
        )

    @classmethod
    def from_mimetype(cls, mime: str) -> FileType:
        """Create FileType from MIME type.

        Parameters
        ----------
        mime : str
            MIME type string (e.g., ``'application/pdf'``, ``'image/jpeg'``).

        Returns
        -------
        FileType
            FileType instance containing all known extensions and the MIME type.

        Examples
        --------
        >>> ft = FileType.from_mimetype('application/pdf')
        >>> '.pdf' in ft.extensions
        True

        >>> ft = FileType.from_mimetype('image/jpeg')
        >>> len(ft.extensions) > 1  # Multiple extensions like .jpg, .jpeg
        True
        """
        extensions = mimetypes.guess_all_extensions(mime, strict=False)
        if not extensions:
            extensions = []

        return cls(
            extensions=tuple(sorted(extensions)),
            mime_types=(mime,),
        )
