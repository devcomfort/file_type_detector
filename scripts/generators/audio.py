"""Audio format generators."""

import struct
import subprocess
import wave
from io import BytesIO

from .base import BaseGenerator
from . import register


@register
class AudioGenerator(BaseGenerator):
    """Generates minimal valid audio files."""

    @property
    def extensions(self) -> list[str]:
        return ["wav", "mid", "midi", "au", "mp3", "flac", "ogg", "oga", "opus", "aiff", "aac"]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "wav": "library:wave",
            "mid": "synthetic:Standard MIDI File header",
            "midi": "synthetic:Standard MIDI File header",
            "au": "synthetic:AU/SND header",
            "mp3": "library:ffmpeg",
            "flac": "synthetic:FLAC stream header",
            "ogg": "synthetic:Ogg container header",
            "oga": "synthetic:Ogg container header",
            "opus": "synthetic:Ogg container header",
            "aiff": "synthetic:AIFF FORM header",
            "aac": "library:ffmpeg",
        }

    @property
    def category(self) -> str:
        return "audio"

    def generate(self, ext: str) -> bytes:
        generators = {
            "wav": self._create_wav,
            "mid": self._create_midi,
            "midi": self._create_midi,
            "au": self._create_au,
            "mp3": self._create_mp3,
            "flac": self._create_flac,
            "ogg": self._create_ogg,
            "oga": self._create_ogg,
            "opus": self._create_ogg,
            "aiff": self._create_aiff,
            "aac": self._create_aac,
        }
        return generators[ext]()

    def _create_wav(self) -> bytes:
        buf = BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(1)
            wf.setframerate(8000)
            wf.writeframes(b"\x80")
        return buf.getvalue()

    def _create_midi(self) -> bytes:
        return (
            b"MThd" + struct.pack(">I", 6) + struct.pack(">HHH", 0, 1, 480)
            + b"MTrk" + struct.pack(">I", 4) + b"\x00\xff\x2f\x00"
        )

    def _create_au(self) -> bytes:
        return b".snd" + struct.pack(">IIIIII", 24, 8, 1, 8000, 1, 0)

    def _create_mp3(self) -> bytes:
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono",
             "-t", "1", "-b:a", "128k", "-f", "mp3", "-"],
            capture_output=True, check=True,
        )
        return result.stdout

    def _create_flac(self) -> bytes:
        return b"fLaC" + struct.pack(">BBI", 0x80, 0, 34) + b"\x00" * 34

    def _create_ogg(self) -> bytes:
        return (
            b"OggS" + b"\x00\x02" + struct.pack("<q", 0)
            + struct.pack("<II", 1, 0) + struct.pack("<I", 0)
            + b"\x01\x00"
        )

    def _create_aiff(self) -> bytes:
        return (
            b"FORM" + struct.pack(">I", 54) + b"AIFF"
            + b"COMM" + struct.pack(">I", 18)
            + struct.pack(">hHI", 1, 1, 8000)
            + struct.pack(">H", 8) + b"\x40\x0e\xac\x44\x00\x00\x00\x00\x00\x00"
            + b"SSND" + struct.pack(">I", 10) + struct.pack(">II", 0, 0) + b"\x80"
        )

    def _create_aac(self) -> bytes:
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono",
             "-t", "1", "-b:a", "128k", "-f", "adts", "-"],
            capture_output=True, check=True,
        )
        return result.stdout
