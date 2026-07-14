"""Executable format generators."""

import struct

from .base import BaseGenerator
from . import register


@register
class ExecutableGenerator(BaseGenerator):
    """Generates minimal valid executable/binary files."""

    @property
    def extensions(self) -> list[str]:
        return ["elf", "so", "ko", "pyc", "pyo"]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "elf": "synthetic:ELF header",
            "so": "synthetic:ELF header",
            "ko": "synthetic:ELF header",
            "pyc": "library:Python compile",
            "pyo": "library:Python compile",
        }

    @property
    def category(self) -> str:
        return "executable"

    def generate(self, ext: str) -> bytes:
        generators = {
            "elf": self._create_elf,
            "so": self._create_elf,
            "ko": self._create_elf,
            "pyc": self._create_pyc,
            "pyo": self._create_pyc,
        }
        return generators[ext]()

    def _create_elf(self) -> bytes:
        return (
            b"\x7fELF" + struct.pack("<BBB", 2, 1, 1) + b"\x00" * 9
            + struct.pack("<H", 2) + struct.pack("<H", 0x3e)
            + struct.pack("<I", 1) + b"\x00" * 20
        )

    def _create_pyc(self) -> bytes:
        return struct.pack("<I", 3439) + struct.pack("<I", 0) + struct.pack("<I", 0) + b"\x00" * 20
