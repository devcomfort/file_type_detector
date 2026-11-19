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
    Abstract base class for all inferencers. Defines the :meth:`~BaseInferencer.detect`
    method that takes a file path and returns a :class:`FileType`.

FileType
    Immutable data class that stores the inferred file extension tuple and
    MIME type tuple.

UnifiedInferencer
    Single entry point that accepts a backend name and routes detection.

    Backend Options:

    - ``"lexical"``: Infers extension from file path only. Fastest but lowest accuracy.
    - ``"magic"``: Analyzes file magic bytes to determine MIME type. Reliable for most files.
    - ``"magika"``: Uses deep learning model for file type inference. Best for text-based files.
    - ``"hybrid"``: Classifies with Magic first, then re-analyzes text files with Magika.
      Provides good balance of speed and accuracy.
    - ``"tika"``: Detects with a pinned Apache Tika build. Requires Java and
      the pinned JAR; OS-independent labels.

BackendType
    String literal type for supported backend options in UnifiedInferencer.
    (``"lexical"`` | ``"magic"`` | ``"magika"`` | ``"hybrid"`` | ``"tika"``)

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

TikaInferencer
    Runs a pinned Apache Tika build in a long-lived JVM process. MIME and
    extension labels are identical across operating systems.

Examples
--------
Basic usage with UnifiedInferencer:

    >>> from filetype_detector import UnifiedInferencer, FileType
    >>> inferencer = UnifiedInferencer("magic")
    >>> result = inferencer.infer("sample.pdf")
    >>> print(result)
    FileType(extensions=('.pdf',), mime_types=('application/pdf',))

Different inference strategies by backend:

    >>> from filetype_detector import UnifiedInferencer
    >>> # Very fast path-based inference
    >>> lex = UnifiedInferencer("lexical")
    >>> lex.infer("archive.zip")

    >>> # Accurate content-based inference
    >>> mag = UnifiedInferencer("magic")
    >>> mag.infer("no_extension_file")

    >>> # High-accuracy deep learning inference (slower)
    >>> magika = UnifiedInferencer("magika")
    >>> magika.infer("script")

    >>> # Balanced speed and accuracy (recommended)
    >>> hybrid = UnifiedInferencer("hybrid")
    >>> hybrid.infer("document")

    >>> # OS-independent labels via Apache Tika (needs Java)
    >>> tika = UnifiedInferencer("tika")
    >>> tika.detect("document.pdf")

Direct inferencer selection:

    >>> from filetype_detector import MagicInferencer, LexicalInferencer
    >>> magic_inf = MagicInferencer()
    >>> lexical_inf = LexicalInferencer()
"""

from .core import FileType, BaseInferencer
from .core import BaseInferencer, FileType
from .strategies import (
    LexicalInferencer,
    MagicInferencer,
    MagikaInferencer,
    HybridInferencer,
    TikaInferencer,
)
from .unified_inferencer import BackendType, UnifiedInferencer

__all__ = [
    "BaseInferencer",
    "FileType",
    "BackendType",
    "BaseInferencer",
    "LexicalInferencer",
    "MagicInferencer",
    "MagikaInferencer",
    "HybridInferencer",
    "TikaInferencer",
    "UnifiedInferencer",
]
