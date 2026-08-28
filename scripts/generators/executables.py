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
        elf_ident = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        elf_hdr = elf_ident + struct.pack("<HHIQQQIHHHHHH", 2, 0x3E, 1, 0x400078, 64, 0, 0, 64, 56, 1, 64, 0, 0)
        elf_ph = struct.pack("<IIQQQQQQ", 1, 5, 0, 0x400000, 0x400000, 120, 120, 0x1000)
        code = b"\xb8\x3c\x00\x00\x00\xbf\x00\x00\x00\x00\x0f\x05"
        return (elf_hdr + elf_ph + code).ljust(512, b"\x00")

    def _create_pyc(self) -> bytes:
        import marshal
        import importlib.util
        def dummy(): pass
        pyc_magic = importlib.util.MAGIC_NUMBER
        pyc_header = pyc_magic + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        return pyc_header + marshal.dumps(dummy.__code__)
