"""Cascading inferencer that combines magic and magika inference methods.

This module provides a two-stage inference strategy: first using magic-based
detection for all files, then falling back to Magika AI for detailed type
detection when the file is identified as a text file.
"""

from .base_inferencer import BaseInferencer
from typing import Union
from pathlib import Path
import magic
import mimetypes
from magika import Magika, PredictionMode


class CascadingInferencer(BaseInferencer):
    """Cascading inferencer that combines magic and magika inference methods.

    This inferencer uses a two-stage approach:
    1. First, it uses python-magic to detect the MIME type and extension
    2. If the detected type is a text file (text/* MIME type), it uses Magika
       to perform more detailed content type detection (e.g., python, javascript,
       json, ini, etc.)

    This approach optimizes performance by only using Magika (which is more
    computationally expensive) for text files, where it excels, while using
    the faster magic-based detection for binary files.

    Attributes
    ----------
    None

    Examples
    --------
    >>> inferencer = CascadingInferencer()
    >>> inferencer.infer('script.py')
    '.py'
    >>> inferencer.infer('data.json')
    '.json'
    >>> inferencer.infer('document.pdf')
    '.pdf'
    """

    def infer(self, file_path: Union[Path, str]) -> str:
        """Infer the file format using a cascading two-stage approach.

        First uses magic-based detection. If the result is a text file,
        performs additional Magika-based detection for more specific type
        identification.

        Parameters
        ----------
        file_path : Union[Path, str]
            Path to the file to analyze. Can be a string or `Path` object.

        Returns
        -------
        str
            File extension with leading dot (e.g., `'.pdf'`, `'.txt'`,
            `'.py'`, `'.json'`). For text files, returns the more specific
            type detected by Magika when available.

        Examples
        --------
        >>> inferencer = CascadingInferencer()
        >>> inferencer.infer('script.py')
        '.py'
        >>> inferencer.infer('data.txt')  # May detect as .json if it's JSON content
        '.json'
        >>> inferencer.infer('document.pdf')
        '.pdf'

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the path is not a file.
        RuntimeError
            If MIME type cannot be determined or Magika fails to analyze the file.
        """
        # Convert to string for compatibility
        file_path_str = str(file_path)

        # Validate file exists and is accessible
        path_obj = Path(file_path_str)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path_str}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {file_path_str}")

        # Stage 1: Use magic to detect MIME type
        mime_type = magic.from_file(file_path_str, mime=True)
        if mime_type is None:
            raise RuntimeError(f"Cannot determine MIME type for file: {file_path_str}")

        # Check if it's a text file
        if mime_type.startswith("text/"):
            # Stage 2: Use Magika for detailed text file type detection
            try:
                magika = Magika(prediction_mode=PredictionMode.MEDIUM_CONFIDENCE)
                result = magika.identify_path(path=file_path_str)

                # Extract extension from Magika result
                extensions = result.output.extensions
                # Magika returns extensions as a list, get the first one if available
                if isinstance(extensions, list) and len(extensions) > 0:
                    extension = extensions[0]
                    # Ensure it starts with a dot
                    if not extension.startswith("."):
                        extension = "." + extension
                    return extension
                elif isinstance(extensions, str) and extensions:
                    extension = extensions
                    if not extension.startswith("."):
                        extension = "." + extension
                    return extension
                # If Magika doesn't return a valid extension, fall back to magic result
            except Exception:
                # If Magika fails, fall back to magic-based result
                # Don't raise error, just use the magic result instead
                pass

        # Fallback: Use magic result for non-text files or if Magika fails
        extension = mimetypes.guess_extension(mime_type, strict=True)
        if extension is None:
            raise RuntimeError(
                f"Cannot convert MIME type '{mime_type}' to extension for file: {file_path_str}"
            )
        return extension
