"""Single entry point that routes detection to one backend.

``UnifiedInferencer`` accepts a backend name and exposes one detection API,
:meth:`detect`. The backend can be set per call (``detect(path, "magika")``) or
fixed at construction (``UnifiedInferencer("magika")``).
"""

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from .core import BaseInferencer, FileType
from .strategies import (
    HybridInferencer,
    LexicalInferencer,
    MagicInferencer,
    MagikaInferencer,
)

BackendType = Literal["lexical", "magic", "magika", "hybrid", "tika"]
"""Public backend names accepted by :class:`UnifiedInferencer`."""

_SUPPORTED_BACKENDS: frozenset[str] = frozenset(
    {"lexical", "magic", "magika", "hybrid", "tika"}
)


def _tika_factory() -> BaseInferencer:
    """Import TikaInferencer lazily so Java/Tika absence does not break imports."""
    from .strategies.tika_inferencer import TikaInferencer

    return TikaInferencer()


_BACKEND_FACTORIES: dict[str, Callable[[], BaseInferencer]] = {
    "lexical": LexicalInferencer,
    "magic": MagicInferencer,
    "magika": MagikaInferencer,
    "hybrid": HybridInferencer,
    "tika": _tika_factory,
}


class UnifiedInferencer(BaseInferencer):
    """Detect file type through one interchangeable backend.

    Parameters
    ----------
    backend : BackendType, optional
        Default backend used when :meth:`detect` is called without one.
        Defaults to ``"hybrid"``.

        - ``"lexical"``: Reads extension directly from the path.
        - ``"magic"``: Determines MIME type from file content via libmagic.
        - ``"magika"``: Analyzes content using the Magika model.
        - ``"hybrid"``: Classifies with Magic first, then re-analyzes ambiguous
          results with Magika.
        - ``"tika"``: Detects with a pinned Apache Tika build (requires Java
          and the pinned JAR).

    Examples
    --------
    >>> result = UnifiedInferencer().detect("document.pdf")
    >>> result.extensions
    ('.pdf',)
    >>> result.mime_types
    ('application/pdf',)
    >>> UnifiedInferencer().detect("document.pdf", "magic")
    """

    def __init__(self, backend: BackendType = "hybrid") -> None:
        """Initialize with a default backend.

        Parameters
        ----------
        backend : BackendType
            Default backend for :meth:`detect` calls that omit the argument.
        Raises
        ------
        KeyError
            Raised when ``backend`` is not one of the supported names.
        """
        if backend not in _SUPPORTED_BACKENDS:
            raise KeyError(backend)
        self._default_backend: BackendType = backend
        self._backends: dict[str, BaseInferencer] = {}

    def _resolve(self, backend: BackendType | None) -> BaseInferencer:
        name: str = backend or self._default_backend
        if name not in _SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unsupported backend {name!r}; expected one of "
                f"{sorted(_SUPPORTED_BACKENDS)}"
            )
        if name not in self._backends:
            self._backends[name] = _BACKEND_FACTORIES[name]()
        return self._backends[name]

    def detect(
        self, file_path: Path | str, backend: BackendType | None = None
    ) -> FileType:
        """Detect file type using the selected backend.

        Parameters
        ----------
        file_path : Path or str
            The file path to analyze.
        backend : BackendType, optional
            Override the default backend for this call only. Omit to use the
            backend given to the constructor.

        Returns
        -------
        FileType
            FileType instance containing detected extensions and MIME types.

        Raises
        ------
        FileNotFoundError
            Raised when the file does not exist.
        ValueError
            Raised when the path is not a file or the backend is unknown.
        RuntimeError
            Raised when the backend fails to determine the file type.
        """
        return self._resolve(backend).detect(file_path)


