"""Executable format generators."""

import struct

from .base import BaseGenerator
from . import register


@register
class ExecutableGenerator(BaseGenerator):
    """Generates minimal valid executable/binary files."""

    @property
    def extensions(self) -> list[str]:
        return ["elf", "so", "ko", "pyc", "pyo", "dex", "macho"]

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
            "dex": self._create_dex,
            "macho": self._create_macho,
        }
        return generators[ext]()

    def _create_elf(self) -> bytes:
        elf_ident = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        elf_hdr = elf_ident + struct.pack("<HHIQQQIHHHHHH", 2, 0x3E, 1, 0x400078, 64, 0, 0, 64, 56, 1, 64, 0, 0)
        code = b"\xb8\x3c\x00\x00\x00\xbf\x00\x00\x00\x00\x0f\x05"
        total_filesz = 120 + len(code)
        elf_ph = struct.pack("<IIQQQQQQ", 1, 5, 0, 0x400000, 0x400000, total_filesz, total_filesz, 0x1000)
        return (elf_hdr + elf_ph + code).ljust(512, b"\x00")

    def _create_pyc(self) -> bytes:
        import marshal
        import importlib.util
        code_obj = compile("pass", "<module>", "exec")
        pyc_magic = importlib.util.MAGIC_NUMBER
        pyc_header = pyc_magic + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        return pyc_header + marshal.dumps(code_obj)

    def _create_dex(self) -> bytes:
        import struct
        import zlib
        import hashlib

        header_size = 112
        string_ids_off = 112
        string_data_off = 116
        string_data = bytes([8]) + b"Lsample;\x00"
        string_id_entry = struct.pack("<I", string_data_off)
        pad = b"\x00" * 2
        map_off = string_data_off + len(string_data) + len(pad)

        map_items = [
            struct.pack("<HHI", 0x0000, 0, 1) + struct.pack("<I", 0),
            struct.pack("<HHI", 0x0001, 0, 1) + struct.pack("<I", string_ids_off),
            struct.pack("<HHI", 0x2002, 0, 1) + struct.pack("<I", string_data_off),
            struct.pack("<HHI", 0x1000, 0, 1) + struct.pack("<I", map_off),
        ]
        map_list = struct.pack("<I", len(map_items)) + b"".join(map_items)

        data_off = string_data_off
        data_size = len(string_data) + len(pad) + len(map_list)
        total_file_size = map_off + len(map_list)

        hdr_rest = struct.pack(
            "<IIIIIIIIIIIIIIIIIIII",
            total_file_size,
            header_size,
            0x12345678,
            0, 0,
            map_off,
            1, string_ids_off,
            0, 0,
            0, 0,
            0, 0,
            0, 0,
            0, 0,
            data_size,
            data_off,
        )

        body_from_32 = hdr_rest + string_id_entry + string_data + pad + map_list
        sha1_sig = hashlib.sha1(body_from_32).digest()
        body_from_12 = sha1_sig + body_from_32
        checksum = zlib.adler32(body_from_12) & 0xFFFFFFFF
        return b"dex\n035\x00" + struct.pack("<I", checksum) + body_from_12

    def _create_macho(self) -> bytes:
        import struct
        macho_hdr = struct.pack("<IIIIIIII", 0xfeedfacf, 0x01000007, 3, 2, 1, 72, 0x200085, 0)
        lc_seg = struct.pack("<II16sQQQQIIII", 0x19, 72, b"__PAGEZERO", 0, 0x100000000, 0, 0, 0, 0, 0, 0)
        return (macho_hdr + lc_seg).ljust(512, b"\x00")
