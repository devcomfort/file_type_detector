"""Font format generators."""

import struct

from .base import BaseGenerator
from . import register


@register
class FontGenerator(BaseGenerator):
    """Generates minimal valid font files."""

    @property
    def extensions(self) -> list[str]:
        return ["ttf", "otf", "woff", "ttc"]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "ttf": "synthetic:TrueType offset table header",
            "otf": "synthetic:OpenType offset table header",
            "woff": "synthetic:WOFF header (wraps TTF)",
            "ttc": "synthetic:TTC header",
        }

    @property
    def category(self) -> str:
        return "font"

    def generate(self, ext: str) -> bytes:
        generators = {
            "ttf": self._create_ttf,
            "otf": self._create_otf,
            "woff": self._create_woff,
            "ttc": self._create_ttc,
        }
        return generators[ext]()

    def _create_ttf(self) -> bytes:
        return (
            struct.pack(">I", 0x00010000) + struct.pack(">H", 1)
            + struct.pack(">H", 16) + struct.pack(">H", 0) + struct.pack(">H", 16)
            + b"head" + struct.pack(">II", 0, 12) + struct.pack(">I", 54)
            + struct.pack(">II", 0x00010000, 0) + struct.pack(">I", 0)
            + struct.pack(">I", 0x5F0F3CF5) + struct.pack(">HH", 0, 1000)
            + struct.pack(">q", 0) + struct.pack(">q", 0)
            + struct.pack(">hhhh", 0, 0, 0, 0)
            + struct.pack(">HhHh", 0, 1, 2, 0)
        )

    def _create_otf(self) -> bytes:
        return (
            struct.pack(">I", 0x4F54544F) + struct.pack(">H", 1)
            + struct.pack(">H", 16) + struct.pack(">H", 0) + struct.pack(">H", 16)
            + b"head" + struct.pack(">II", 0, 12) + struct.pack(">I", 54)
            + struct.pack(">II", 0x4F54544F, 0) + struct.pack(">I", 0)
            + struct.pack(">I", 0x5F0F3CF5) + struct.pack(">HH", 0, 1000)
            + struct.pack(">q", 0) + struct.pack(">q", 0)
            + struct.pack(">hhhh", 0, 0, 0, 0)
            + struct.pack(">HhHh", 0, 1, 2, 0)
        )

    def _create_woff(self) -> bytes:
        ttf = self._create_ttf()
        return (
            b"wOFF" + struct.pack(">I", 0x00010000)
            + struct.pack(">I", 44 + len(ttf)) + struct.pack(">H", 1)
            + struct.pack(">H", 0) + struct.pack(">I", 44)
            + struct.pack(">HH", 0, 0) + struct.pack(">I", 0)
            + struct.pack(">I", 0) + struct.pack(">I", 0)
            + struct.pack(">I", 0) + struct.pack(">I", 0)
            + b"head" + struct.pack(">I", 44) + struct.pack(">I", len(ttf))
            + struct.pack(">I", len(ttf)) + struct.pack(">I", 0)
            + ttf
        )

    def _create_ttc(self) -> bytes:
        return b"ttcf" + struct.pack(">I", 0x00010000) + struct.pack(">H", 1) + struct.pack(">H", 0)
