"""Defines the common interface for file type inferencers."""

from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path
from .file_type import FileType


class BaseInferencer(ABC):
    """Abstract base class for file type inferencers.

    All concrete inference strategies must inherit from this class and
    implement the :meth:`infer` method. Provides a shared :meth:`_validate_path`
    utility for file existence and type checking.

    Notes
    -----
    Subclasses should not override :meth:`_validate_path` — it is a static
    utility shared across all strategies.
    """

    @abstractmethod
    def infer(self, file_path: Union[Path, str]) -> FileType:
        """Infer file type from a file path.

        Parameters
        ----------
        file_path : Union[Path, str]
            The path to the file whose type will be inferred.

        Returns
        -------
        FileType
            A FileType instance containing the inferred extension and MIME type.

        Raises
        ------
        NotImplementedError
            Raised when a subclass does not implement this method.
        """
        raise NotImplementedError

    @staticmethod
    def _validate_path(file_path: Union[Path, str]) -> Path:
        """Validate file existence and type, returning a resolved Path.

        Parameters
        ----------
        file_path : Union[Path, str]
            The path to validate.

        Returns
        -------
        Path
            Resolved Path object.

        Raises
        ------
        FileNotFoundError
            Raised when the file does not exist.
        ValueError
            Raised when the path is not a file (e.g., directory).
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path_obj}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path_obj}")
        return path_obj
