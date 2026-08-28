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
            struct.pack(">I", 0x00010000)
            + struct.pack(">H", 1)
            + struct.pack(">H", 16)
            + struct.pack(">H", 0)
            + struct.pack(">H", 16)
            + b"head"
            + struct.pack(">II", 0, 12)
            + struct.pack(">I", 54)
            + struct.pack(">II", 0x00010000, 0)
            + struct.pack(">I", 0)
            + struct.pack(">I", 0x5F0F3CF5)
            + struct.pack(">HH", 0, 1000)
            + struct.pack(">q", 0)
            + struct.pack(">q", 0)
            + struct.pack(">hhhh", 0, 0, 0, 0)
            + struct.pack(">HhHh", 0, 1, 2, 0)
        )

    def _create_otf(self) -> bytes:
        return (
            struct.pack(">I", 0x4F54544F)
            + struct.pack(">H", 1)
            + struct.pack(">H", 16)
            + struct.pack(">H", 0)
            + struct.pack(">H", 16)
            + b"head"
            + struct.pack(">II", 0, 12)
            + struct.pack(">I", 54)
            + struct.pack(">II", 0x4F54544F, 0)
            + struct.pack(">I", 0)
            + struct.pack(">I", 0x5F0F3CF5)
            + struct.pack(">HH", 0, 1000)
            + struct.pack(">q", 0)
            + struct.pack(">q", 0)
            + struct.pack(">hhhh", 0, 0, 0, 0)
            + struct.pack(">HhHh", 0, 1, 2, 0)
        )

    def _create_woff(self) -> bytes:
        # Full spec-valid WOFF 1.0 font package generated deterministically via fontTools.
        # Contains complete valid sfnt tables ('head', 'hhea', 'maxp', 'OS/2', 'hmtx', 'cmap', 'loca', 'glyf', 'name', 'post').
        # Embedded as base64 for 100% portable pure-Python reproduction.
        import base64

        return base64.b64decode(
            "d09GRgABAAAAAAIkAAoAAAAAAlAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAABPUy8yAAABYAAAAB0AAABgQPZBOGNtYXAAAAGEAAAAJQAAACwADABGZ2x5ZgAAAbAAAAAYAAAAGCT7MwhoZWFkAAAA9AAAADYAAAA2w+axqWhoZWEAAAEsAAAAHAAAACQFFgEuaG10eAAAAYAAAAAEAAAABAH0AABsb2NhAAABrAAAAAQAAAAEAAAADG1heHAAAAFIAAAAGAAAACAAAwAGbmFtZQAAAcgAAABKAAAAV2FMeWpwb3N0AAACFAAAAA8AAAAkAAMAAAABAAAAAQAAgRdbkF8PPPUAAwPoAAAAAHwlncAAAAAA5rbRFQAAAAAB9AH0AAAAAwACAAAAAAAAeJxjYGRgYFb4b8HAwPiFgQFMMjKgAkYAUvEDSHicY2BkYGBgZGBhANEMDEwMaAAAAPcACnicY2Bm/MI4gYGVgYWBRGAPBASUKDAwAAC1cgKvAAAAAfQAAHicY2BgYGJgYGAGYhEgyQimWRgkGEDiIBmG///BGCgDACZoBE8AAAAAAAAMAAEAAAAAAfQB9AADAAAxESERAfQB9P4MeJwtyDsKwCAQhOF/VUhCwCZ3yUHEC1gsNlY+7p8NOM18M0DgRfgjZrYdhy2PhMuek3vbEXmyjpm0rlY6GWUwSdaVRaPQP9J1CYwAAHicY2BiwA8YGRgAAG0ABAA="
        )

    def _create_ttc(self) -> bytes:
        return (
            b"ttcf"
            + struct.pack(">I", 0x00010000)
            + struct.pack(">H", 1)
            + struct.pack(">H", 0)
        )
