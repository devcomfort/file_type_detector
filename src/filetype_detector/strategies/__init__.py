"""Strategy implementations for file type inference.

This package contains concrete implementations of the
:class:`~filetype_detector.core.BaseInferencer` interface, each representing
a different approach to file type detection:

- :class:`LexicalInferencer`: Extension-only extraction (fastest).
- :class:`MagicInferencer`: Magic byte analysis via libmagic.
- :class:`MagikaInferencer`: AI-powered detection via Google Magika.
- :class:`HybridInferencer`: Magic + Magika cascade (recommended default).
"""

from .lexical_inferencer import LexicalInferencer
from .magic_inferencer import MagicInferencer
from .magika_inferencer import MagikaInferencer
from .hybrid_inferencer import HybridInferencer

__all__ = [
    "LexicalInferencer",
    "MagicInferencer",
    "MagikaInferencer",
    "HybridInferencer",
]
