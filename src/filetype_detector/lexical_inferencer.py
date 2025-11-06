from .base_inferencer import BaseInferencer
from typing import Union
from pathlib import Path


class LexicalInferencer(BaseInferencer):
    """Lexical inferencer that uses the file path to infer the file format.

    This inferencer extracts the file extension from the provided path using
    `pathlib.Path`. It is a lightweight, content‑agnostic implementation
    that fits into the unified inference interface.

    Attributes
    ----------
    None
    """

    def infer(self, file_path: Union[Path, str]) -> str:
        """Infer the file format from the file path.

        Parameters
        ----------
        file_path : Union[Path, str]
            Path to the file. Can be a `Path` object or a string representing
            the file system path.

        Returns
        -------
        str
            File extension in lowercase with leading dot (e.g., `'.txt'`,
            `'.pdf'`). Returns an empty string if the file has no extension.

        Examples
        --------
        >>> inferencer = LexicalInferencer()
        >>> inferencer.infer('document.pdf')
        '.pdf'
        >>> inferencer.infer(Path('data.txt'))
        '.txt'
        >>> inferencer.infer('no_extension')
        ''
        """
        return Path(file_path).suffix.lower()
