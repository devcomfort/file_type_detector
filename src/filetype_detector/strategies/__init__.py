"""Strategy implementations for file type inference.

This package contains concrete implementations of the
:class:`~filetype_detector.core.BaseInferencer` interface, each representing
a different approach to file type detection:

- :class:`LexicalInferencer`: Extension-only extraction (fastest).
- :class:`MagikaInferencer`: AI-powered detection via Google Magika.
- :class:`HybridInferencer`: Magic + Magika cascade (recommended default).
- :class:`TikaInferencer`: Apache Tika with OS-independent labels.
"""
from .lexical_inferencer import LexicalInferencer
from .magic_inferencer import MagicInferencer
from .magika_inferencer import MagikaInferencer
from .hybrid_inferencer import HybridInferencer
from .tika_inferencer import TikaInferencer

__all__ = [
    "LexicalInferencer",
    "MagicInferencer",
    "MagikaInferencer",
    "HybridInferencer",
    "TikaInferencer",
]
