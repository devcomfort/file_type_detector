"""Base file loader inferencer module.

Provides an abstract base class for inferring file formats from a given path.
"""

from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path


class BaseInferencer(ABC):
    """Abstract base class for file format inference.

    Subclasses must implement the `infer` method to return a string
    identifier of the inferred file format.

    Attributes
    ----------
    None
    """

    @abstractmethod
    def infer(self, file_path: Union[Path, str]) -> str:
        """Infer the file format from a path.

        Parameters
        ----------
        file_path : Union[Path, str]
            Path to the file whose format should be inferred. Can be a `Path`
            object or a string representing the file system path.

        Returns
        -------
        str
            The inferred file format identifier, e.g., `'pdf'`, `'txt'`,
            `'image'`, etc.

        Raises
        ------
        NotImplementedError
            If the subclass does not implement this method.
        """
        raise NotImplementedError
