"""Video format generators."""

import struct

from .base import BaseGenerator
from . import register


@register
class VideoGenerator(BaseGenerator):
    """Generates minimal valid video files."""

    @property
    def extensions(self) -> list[str]:
        return ["mp4", "mkv", "webm", "avi", "mov", "3gp", "flv", "ts", "m2t"]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "mp4": "synthetic:ISO BMFF ftyp box",
            "mkv": "synthetic:Matroska EBML header",
            "webm": "synthetic:WebM EBML header",
            "avi": "synthetic:RIFF AVI header",
            "mov": "synthetic:QuickTime ftyp box",
            "3gp": "synthetic:3GPP ftyp box",
            "flv": "synthetic:FLV header",
            "ts": "synthetic:MPEG-TS packet header",
            "m2t": "synthetic:MPEG-TS packet header",
        }

    @property
    def category(self) -> str:
        return "video"

    def generate(self, ext: str) -> bytes:
        generators = {
            "mp4": self._create_mp4,
            "mkv": self._create_mkv,
            "webm": self._create_webm,
            "avi": self._create_avi,
            "mov": self._create_mov,
            "3gp": self._create_3gp,
            "flv": self._create_flv,
            "ts": self._create_ts,
            "m2t": self._create_ts,
        }
        return generators[ext]()

    def _create_mp4(self) -> bytes:
        return (
            struct.pack(">I", 32)
            + b"ftyp"
            + b"isom"
            + struct.pack(">I", 0)
            + b"isomiso2mp41"
            + struct.pack(">I", 8)
            + b"free"
        )

    def _create_mkv(self) -> bytes:
        return (
            b"\x1a\x45\xdf\xa3"
            + b"\x01\x00\x00\x00\x00\x00\x00\x1c"
            + b"\x42\x86"
            + b"\x81\x01"
            + b"\x42\xf7"
            + b"\x81\x01"
            + b"\x42\xf2"
            + b"\x81\x04"
            + b"\x42\xf3"
            + b"\x81\x08"
            + b"\x42\x82"
            + b"\x88\x6d\x61\x74\x72\x6f\x73\x6b\x61"
        )

    def _create_webm(self) -> bytes:
        # Decodable valid minimal WebM video stream generated deterministically via ffmpeg (lavfi color vp9).
        # Embedded as base64 for 100% portable pure-Python generation without ffmpeg runtime dependency.
        import base64

        return base64.b64decode(
            "GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQJChYECGFOAZwH/////////EU2bdKtNu4tTq4QVSalmU6yBoU27i1OrhBZUrmtTrIHYTbuMU6uEElTDZ1OsggEi7AEAAAAAAABoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVSalmsirXsYMPQkBNgI1MYXZmNTguNzYuMTAwV0GNTGF2ZjU4Ljc2LjEwMESJiEBZAAAAAAAAFlSua8WuAQAAAAAAADzXgQFzxYjOk3xd4FAQQ5yBACK1nIN1bmSGhVZfVlA5g4EBI+ODhAX14QDgAQAAAAAAAAmwgRC6gRCagQISVMNn+XNzAQAAAAAAACdjwIBnyAEAAAAAAAAaRaOHRU5DT0RFUkSHjUxhdmY1OC43Ni4xMDBzcwEAAAAAAAA+Y8CLY8WIzpN8XeBQEENnyAEAAAAAAAAmRaOHRU5DT0RFUkSHmUxhdmM1OC4xMzQuMTAwIGxpYnZweC12cDkfQ7Z1sOeBAKOrgQAAgIJJg0IAAPAA9gA4JBwYSgAAMGAAABC///wQsf////8irP///n/AAA=="
        )

    def _create_avi(self) -> bytes:
        return (
            b"RIFF"
            + struct.pack("<I", 100)
            + b"AVI LIST"
            + struct.pack("<I", 92)
            + b"hdrl"
            + b"avih"
            + struct.pack("<I", 56)
            + struct.pack("<IIII", 0, 0, 0, 0)
            + b"\x00" * 40
            + b"LIST"
            + struct.pack("<I", 0)
            + b"movi"
        )

    def _create_mov(self) -> bytes:
        return (
            struct.pack(">I", 24)
            + b"ftyp"
            + b"qt  "
            + struct.pack(">I", 0)
            + b"qt  "
            + struct.pack(">I", 8)
            + b"free"
        )

    def _create_3gp(self) -> bytes:
        return (
            struct.pack(">I", 28)
            + b"ftyp"
            + b"3gp4"
            + struct.pack(">I", 0)
            + b"3gp4isom"
            + struct.pack(">I", 8)
            + b"free"
        )

    def _create_flv(self) -> bytes:
        return b"FLV" + b"\x01" + b"\x00" + struct.pack(">I", 9) + struct.pack(">I", 0)

    def _create_ts(self) -> bytes:
        return b"\x47\x40\x00\x10" + b"\x00" * 184
