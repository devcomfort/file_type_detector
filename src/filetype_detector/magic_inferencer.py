from .base_inferencer import BaseInferencer
from typing import Union
from pathlib import Path
import mimetypes
import magic


class MagicInferencer(BaseInferencer):
    """Magic inferencer that uses python-magic to infer the file format.

    Attributes
    ----------
    None
    """

    def infer(self, file_path: Union[Path, str]) -> str:
        """Infer file extension using python-magic and mimetypes.

        Parameters
        ----------
        file_path : Union[Path, str]
            Path to the file to analyze. Can be a string or `Path` object.

        Returns
        -------
        str
            File extension with leading dot (e.g., `'.pdf'`, `'.txt'`).
            Never returns an empty string as `RuntimeError` is raised if
            the MIME type cannot be converted to an extension.

        Examples
        --------
        >>> inferencer = MagicInferencer()
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
            If the MIME type cannot be determined or converted to an extension.
        """
        # Convert to string for compatibility
        file_path_str = str(file_path)
        # Validate file exists and is accessible
        path_obj = Path(file_path_str)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path_str}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {file_path_str}")
        # Use python-magic to detect MIME type from file content
        mime_type = magic.from_file(file_path_str, mime=True)
        if mime_type is None:
            raise RuntimeError(f"Cannot determine MIME type for file: {file_path_str}")
        # Convert MIME type to extension using mimetypes
        extension = mimetypes.guess_extension(mime_type, strict=True)
        if extension is None:
            raise RuntimeError(
                f"Cannot convert MIME type '{mime_type}' to extension for file: {file_path_str}"
            )
        return extension
