"""File format inference module.

This module provides type definitions and a centralized mapping of available
file format inference implementations. It allows users to easily switch between
different file type detection methods by using simple string keys to access
the appropriate inference function.

Available inference methods:
- None: Simple path-based extension extraction without content inference
- magika: Google's AI-powered content type detection with confidence scores
- magic: Traditional libmagic-based MIME type detection with extension conversion

Example:
    >>> from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP
    >>>
    >>> # Type-safe usage with different strategies
    >>> def process_file(file_path: str, method: InferencerType) -> str:
    ...     inferencer = FILE_FORMAT_INFERENCER_MAP[method]
    ...     if method == "magika":
    ...         extension, score = inferencer(file_path)
    ...         return f"{extension} (confidence: {score:.2f})"
    ...     elif method == "magic":
    ...         extension = inferencer(file_path)
    ...         return extension
    ...     else:  # method is None
    ...         extension = inferencer(file_path)
    ...         return extension
    >>>
    >>> # ===== BASIC USAGE =====
    >>> # Path-based extraction (fastest, relies on file extension)
    >>> inferencer = FILE_FORMAT_INFERENCER_MAP[None]
    >>> extension = inferencer("document.pdf")
    >>> print(f"Extension: {extension}")
    Extension: .pdf
    >>>
    >>> # AI-powered inference with confidence scores
    >>> inferencer = FILE_FORMAT_INFERENCER_MAP["magika"]
    >>> extension, score = inferencer("document.pdf")
    >>> print(f"Extension: {extension}, Confidence: {score:.2f}")
    Extension: pdf, Confidence: 0.98
    >>>
    >>> # Traditional libmagic-based inference
    >>> inferencer = FILE_FORMAT_INFERENCER_MAP["magic"]
    >>> extension = inferencer("document.pdf")
    >>> print(f"Extension: {extension}")
    Extension: .pdf

Note:
    The None option provides a performance-optimized path for cases where
    file content analysis is unnecessary, such as when file extensions are
    known to be accurate or when working with trusted file sources.

    python-magic uses libmagic's extensive database of file signatures to
    detect file types based on magic numbers and content patterns, making it
    highly reliable for content-based file type identification, especially
    for files with incorrect or missing extensions.
"""

from typing import Literal, Union, Callable
from pathlib import Path

from .lexical_inferencer import LexicalInferencer
from .magic_inferencer import MagicInferencer
from .magika_inferencer import MagikaInferencer


InferencerType = Union[Literal["magika", "magic"], None]
"""Type alias for available file format inference methods.

This union type restricts the inference method selection to the supported
algorithms or None for simple path-based extension extraction, ensuring
type safety when working with different file type detection strategies.

Available methods:
- `"magika"`: Google's AI-powered content type detection with confidence scores
- `"magic"`: Traditional libmagic-based MIME type detection with extension conversion
- `None`: Simple path-based extension extraction without content inference

Example:
    >>> from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP
    >>>
    >>> def process_file(file_path: str, method: InferencerType) -> str:
    ...     inferencer = FILE_FORMAT_INFERENCER_MAP[method]
    ...     if method == "magika":
    ...         extension, score = inferencer(file_path)
    ...         return f"{extension} (confidence: {score:.2f})"
    ...     elif method == "magic":
    ...         extension = inferencer(file_path)
    ...         return extension
    ...     else:  # method is None
    ...         extension = inferencer(file_path)
    ...         return extension
    >>>
    >>> # Type-safe usage with different strategies
    >>> result1 = process_file("document.pdf", "magika")  # AI-powered inference
    >>> result2 = process_file("document.pdf", "magic")   # libmagic-based inference
    >>> result3 = process_file("document.pdf", None)      # Path-based extraction
    >>> result4 = process_file("document.pdf", "invalid") # Type error

Note:
    Using None as the inference method provides a lightweight option for cases
    where file content analysis is not required and the file extension can be
    trusted. This is useful for performance-critical scenarios or when working
    with known file types.
"""


FILE_FORMAT_INFERENCER_MAP: dict[InferencerType, Callable[[Union[Path, str]], str]] = {
    None: lambda path: LexicalInferencer().infer(path),
    "magic": lambda path: MagicInferencer().infer(path),
    "magika": lambda path: MagikaInferencer().infer(path),
}
"""A dictionary mapping inferencer type keys to their corresponding file type detection functions.

This mapping allows you to easily switch between different file type detection strategies
by using simple string keys. Each key corresponds to a different approach for determining
the actual file format based on either the file extension or the file's content.

Available keys and their meanings:

- `None`: Uses the lexical inferencer that simply extracts the file extension from the
  filename. This is the fastest method but relies on the extension being accurate.
  
- `"magic"`: Uses the python-magic library to analyze the file's content and detect
  the actual file type based on magic numbers. This is useful when file extensions
  are missing, incorrect, or misleading.
  
- `"magika"`: Uses Google's Magika AI model to predict the file type with a confidence
  score. This provides the most advanced content-based detection but may be slower.

Example usage:
    >>> from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP
    >>> 
    >>> # Get the lexical inferencer (fastest)
    >>> infer = FILE_FORMAT_INFERENCER_MAP[None]
    >>> print(infer('document.pdf'))
    '.pdf'
    >>> 
    >>> # Get the magic-based inferencer (content analysis)
    >>> infer = FILE_FORMAT_INFERENCER_MAP['magic']
    >>> print(infer('file_with_wrong_extension.dat'))
    '.pdf'
    >>> 
    >>> # ===== MISLEADING EXTENSIONS =====
    >>> # File with .txt extension but contains JSON content
    >>> inferencer = FILE_FORMAT_INFERENCER_MAP["magika"]
    >>> extension, score = inferencer("data.txt")
    >>> print(f"Actual content: {extension}, Confidence: {score:.2f}")
    Actual content: json, Confidence: 0.95
    >>> 
    >>> inferencer = FILE_FORMAT_INFERENCER_MAP["magic"]
    >>> extension = inferencer("data.txt")
    >>> print(f"Actual content: {extension}")
    Actual content: .json
"""
