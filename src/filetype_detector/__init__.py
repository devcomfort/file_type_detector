"""Automatic file type detection package.

This package provides tools to infer file extensions and MIME types using
multiple inference strategies.

Architecture
------------
The library follows a strategy pattern with two layers:

- ``core/``: Domain types (:class:`FileType`) and the abstract interface
  (:class:`BaseInferencer`).
- ``strategies/``: Concrete implementations of each inference approach.

Public API
----------
BaseInferencer
    Abstract base class for all inferencers. Defines the :meth:`~BaseInferencer.infer`
    method that takes a file path and returns a :class:`FileType`.

FileType
    Immutable data class that stores the inferred file extension tuple and
    MIME type tuple.

AutoInferencer
    Factory class that accepts a string backend key and selects the appropriate
    inferencer implementation.

    Backend Options:

    - ``"lexical"``: Infers extension from file path only. Fastest but lowest accuracy.
    - ``"magic"``: Analyzes file magic bytes to determine MIME type. Reliable for most files.
    - ``"magika"``: Uses deep learning model for file type inference. Best for text-based files.
    - ``"hybrid"``: Classifies with Magic first, then re-analyzes text files with Magika.
      Provides good balance of speed and accuracy.

BackendType
    String literal type for supported backend options in AutoInferencer.
    (``"lexical"`` | ``"magic"`` | ``"magika"`` | ``"hybrid"``)

LexicalInferencer
    Infers extension from file path only. Fastest but lowest accuracy.

MagicInferencer
    Analyzes file magic bytes (magic number) to infer MIME type and extension.

MagikaInferencer
    Uses deep learning model to infer file format. Excels at distinguishing
    detailed types of text-based files.

HybridInferencer
    Combines Magic and Magika strategies sequentially. Fast for binary files,
    precise for text files.

Examples
--------
Basic usage with AutoInferencer:

    >>> from filetype_detector import AutoInferencer, FileType
    >>> inferencer = AutoInferencer("magic")
    >>> result = inferencer.infer("sample.pdf")
    >>> print(result)
    FileType(extensions=('.pdf',), mime_types=('application/pdf',))

Different inference strategies by backend:

    >>> from filetype_detector import AutoInferencer
    >>> # Very fast path-based inference
    >>> lex = AutoInferencer("lexical")
    >>> lex.infer("archive.zip")

    >>> # Accurate content-based inference
    >>> mag = AutoInferencer("magic")
    >>> mag.infer("no_extension_file")

    >>> # High-accuracy deep learning inference (slower)
    >>> magika = AutoInferencer("magika")
    >>> magika.infer("script")

    >>> # Balanced speed and accuracy (recommended)
    >>> hybrid = AutoInferencer("hybrid")
    >>> hybrid.infer("document")

Direct inferencer selection:

    >>> from filetype_detector import MagicInferencer, LexicalInferencer
    >>> magic_inf = MagicInferencer()
    >>> lexical_inf = LexicalInferencer()
"""

from .core import FileType, BaseInferencer
from .auto_inferencer import AutoInferencer, BackendType
from .strategies import (
    LexicalInferencer,
    MagicInferencer,
    MagikaInferencer,
    HybridInferencer,
)

__all__ = [
    "BaseInferencer",
    "FileType",
    "AutoInferencer",
    "BackendType",
    "LexicalInferencer",
    "MagicInferencer",
    "MagikaInferencer",
    "HybridInferencer",
]
