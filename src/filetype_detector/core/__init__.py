"""Core domain types and base interfaces.

This package contains the foundational building blocks of the filetype-detector
library:

- :class:`~filetype_detector.core.FileType`: Immutable data class holding
  extensions and MIME types.
- :class:`~filetype_detector.core.BaseInferencer`: Abstract base class that
  all inference strategies must implement.
"""

from .base_inferencer import BaseInferencer
from .file_type import FileType

__all__ = ["BaseInferencer", "FileType"]
