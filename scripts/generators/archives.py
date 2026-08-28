"""Archive fixture generators with byte-reproducible output."""

from io import BytesIO
import bz2
import lz4.frame
import struct
import tarfile
import zipfile
import zstandard

from ._deterministic import write_zip_str, gzip_compress_det
from .base import BaseGenerator
from . import register


@register
class ArchiveGenerator(BaseGenerator):
    """Generates minimal valid archive files."""

    @property
    def extensions(self) -> list[str]:
        return [
            "zip",
            "tar",
            "gz",
            "tgz",
            "bz2",
            "tbz2",
            "xz",
            "lz",
            "lz4",
            "zst",
            "7z",
            "xpi",
            "jar",
            "apk",
            "gzip",
            "nupkg",
            "maff",
            "tar.gz",
            "tar.bz2",
            "rz",
            "arc",
            "lha",
            "lrz",
            "lzh",
            "pkg",
            "rpm",
            "snap",
            "wad",
            "xar",
            "z",
        ]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "zip": "library:zipfile",
            "tar": "library:tarfile",
            "gz": "library:gzip",
            "tgz": "library:gzip",
            "tar.gz": "library:gzip",
            "bz2": "library:bz2",
            "tbz2": "library:bz2",
            "tar.bz2": "library:bz2",
            "xz": "library:lzma",
            "lz": "library:lzma",
            "lz4": "library:lz4",
            "zst": "library:zstandard",
            "7z": "library:py7zr",
            "xpi": "library:zipfile",
            "jar": "library:zipfile",
            "apk": "library:zipfile",
            "gzip": "library:gzip",
            "nupkg": "library:zipfile",
            "maff": "library:zipfile",
            "rz": "library:gzip",
            "arc": "synthetic:ARC magic bytes",
            "lha": "synthetic:LHA magic bytes",
            "lrz": "synthetic:LRZIP magic bytes",
            "lzh": "synthetic:LZH magic bytes",
            "pkg": "synthetic:XAR wrapper (macOS package)",
            "rpm": "synthetic:RPM magic bytes",
            "snap": "synthetic:SquashFS magic bytes",
            "wad": "synthetic:WAD magic bytes",
            "xar": "synthetic:XAR magic bytes",
            "z": "synthetic:Unix compress magic bytes",
        }

    @property
    def category(self) -> str:
        return "archive"

    def generate(self, ext: str) -> bytes:
        generators = {
            "zip": self._create_zip,
            "tar": self._create_tar,
            "gz": self._create_gz,
            "tgz": self._create_gz,
            "tar.gz": self._create_gz,
            "bz2": self._create_bz2,
            "tbz2": self._create_bz2,
            "tar.bz2": self._create_bz2,
            "xz": self._create_xz,
            "lz": self._create_lz,
            "lz4": self._create_lz4,
            "zst": self._create_zst,
            "7z": self._create_7z,
            "xpi": self._create_zip,
            "jar": self._create_zip,
            "apk": self._create_zip,
            "gzip": self._create_gz,
            "nupkg": self._create_nupkg,
            "maff": self._create_maff,
            "rz": self._create_rz,
            "arc": self._create_arc,
            "lha": self._create_lha,
            "lrz": self._create_lrz,
            "lzh": self._create_lzh,
            "pkg": self._create_pkg,
            "rpm": self._create_rpm,
            "snap": self._create_snap,
            "wad": self._create_wad,
            "xar": self._create_xar,
            "z": self._create_z,
        }
        return generators[ext]()

    def _create_zip(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(zf, "hello.txt", "Hello, World!\n")
        return buf.getvalue()

    def _create_tar(self) -> bytes:
        buf = BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            data = b"Hello, World!\n"
            info = tarfile.TarInfo(name="hello.txt")
            info.size = len(data)
            tf.addfile(info, BytesIO(data))
        return buf.getvalue()

    def _create_gz(self) -> bytes:
        return gzip_compress_det(b"Hello, World!\n")

    def _create_bz2(self) -> bytes:
        return bz2.compress(b"Hello, World!\n")

    def _create_xz(self) -> bytes:
        import lzma

        return lzma.compress(b"Hello, World!\n")

    def _create_lz(self) -> bytes:
        import lzma

        return lzma.compress(b"Hello, World!\n", format=lzma.FORMAT_ALONE)

    def _create_lz4(self) -> bytes:
        return lz4.frame.compress(b"Hello, World!\n")

    def _create_zst(self) -> bytes:
        cctx = zstandard.ZstdCompressor()
        return cctx.compress(b"Hello, World!\n")

    def _create_7z(self) -> bytes:
        import py7zr

        buf = BytesIO()
        with py7zr.SevenZipFile(buf, "w") as archive:
            archive.writestr(b"Hello, World!\n", "hello.txt")
        return buf.getvalue()

    def _create_nupkg(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "sample.nuspec",
                '<?xml version="1.0"?><package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"><metadata><id>Sample</id><version>1.0.0</version><description>Sample package</description></metadata></package>',
            )
        return buf.getvalue()

    def _create_maff(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(zf, "index.html", "<html><body>Sample</body></html>")
        return buf.getvalue()

    def _create_rz(self) -> bytes:
        return gzip_compress_det(b"Hello, World!\n")

    def _create_arc(self) -> bytes:
        return b"\x1a" + b"\x00" * 20

    def _create_lha(self) -> bytes:
        name = b"sample.txt"
        body = b"Hello, World!"
        method = b"-lh0-"
        hdr_data = (
            method
            + struct.pack("<III", len(body), len(body), 0)
            + b"\x20\x01"
            + bytes([len(name)])
            + name
            + b"\x00\x00U\x00\x00"
        )
        hdr = bytes([len(hdr_data) + 1, sum(hdr_data) & 0xFF]) + hdr_data
        return hdr + body + b"\x00"

    def _create_lrz(self) -> bytes:
        return b"LRZI" + b"\x00" * 20

    def _create_lzh(self) -> bytes:
        return b"-lh0-" + b"\x00" * 20

    def _create_pkg(self) -> bytes:
        return b"xar!\x00\x01" + struct.pack(">I", 28) + b"\x00" * 16

    def _create_rpm(self) -> bytes:
        import gzip
        lead = (
            b"\xed\xab\xee\xdb"
            + bytes([3, 0])
            + struct.pack(">hh", 0, 1)
            + b"sample".ljust(66, b"\x00")
            + struct.pack(">hh", 1, 5)
            + b"\x00" * 16
        )
        sig_hdr_magic = b"\x8e\xad\xe8\x01\x00\x00\x00\x00"
        sig_idx = struct.pack(">IIII", 1000, 4, 0, 1)
        sig_data = struct.pack(">I", 0)
        sig_pad_len = (8 - (len(sig_hdr_magic) + 16 + len(sig_data)) % 8) % 8
        sig_header = (
            sig_hdr_magic
            + struct.pack(">II", 1, len(sig_data))
            + sig_idx
            + sig_data
            + (b"\x00" * sig_pad_len)
        )
        main_hdr_magic = b"\x8e\xad\xe8\x01\x00\x00\x00\x00"
        strings = [b"sample\x00", b"1.0\x00", b"1\x00", b"cpio\x00", b"gzip\x00"]
        str_offsets = []
        curr_off = 0
        for s in strings:
            str_offsets.append(curr_off)
            curr_off += len(s)
        main_data = b"".join(strings)
        main_indices = [
            struct.pack(">IIII", 1000, 6, str_offsets[0], 1),
            struct.pack(">IIII", 1001, 6, str_offsets[1], 1),
            struct.pack(">IIII", 1002, 6, str_offsets[2], 1),
            struct.pack(">IIII", 1124, 6, str_offsets[3], 1),
            struct.pack(">IIII", 1125, 6, str_offsets[4], 1),
        ]
        main_header = (
            main_hdr_magic
            + struct.pack(">II", len(main_indices), len(main_data))
            + b"".join(main_indices)
            + main_data
        )
        filename = b"sample.txt\x00"
        filedata = b"Hello, World!\n"
        cpio_hdr = (
            b"070701"
            + b"00000001"
            + b"000081a4"
            + b"00000000"
            + b"00000000"
            + b"00000001"
            + b"00000000"
            + f"{len(filedata):08x}".encode("ascii")
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + f"{len(filename):08x}".encode("ascii")
            + b"00000000"
        )
        cpio_pad1 = (4 - (len(cpio_hdr) + len(filename)) % 4) % 4
        cpio_pad2 = (4 - len(filedata) % 4) % 4
        trailer_name = b"TRAILER!!!\x00"
        trailer_hdr = (
            b"070701"
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + b"00000001"
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + b"00000000"
            + f"{len(trailer_name):08x}".encode("ascii")
            + b"00000000"
        )
        trailer_pad = (4 - (len(trailer_hdr) + len(trailer_name)) % 4) % 4
        cpio_archive = (
            cpio_hdr
            + filename
            + (b"\x00" * cpio_pad1)
            + filedata
            + (b"\x00" * cpio_pad2)
            + trailer_hdr
            + trailer_name
            + (b"\x00" * trailer_pad)
        )
        payload = gzip.compress(cpio_archive, mtime=0)
        return lead + sig_header + main_header + payload

    def _create_snap(self) -> bytes:
        # Pinned byte-deterministic SquashFS 4.0 filesystem image containing sample.txt ("Hello, World!\n").
        # Generated reproducibly via mksquashfs with -mkfs-time 0, -reproducible, and fixed utime(0, 0).
        # Embedded directly as base64 to ensure 100% portable generation across macOS/Windows/Linux without mksquashfs.
        import base64
        return base64.b64decode(
            "aHNxcwIAAAAAAAAAAAACAAEAAAABABEAwAABAAQAAAAgAAAAAAAAAO0AAAAAAAAA5QAAAAAAAAD//////////24AAAAAAAAAjwAAAAAAAAC/AAAAAAAAANcAAAAAAAAASGVsbG8sIFdvcmxkIQofAHjaY2LYwsgABXAGFPCBxf7ChZmQaEUgZgZiAE34Ae4cAHjaY2CAAEYozcTAyVCcmFuQk6pXUlECABcUBB0QgGAAAAAAAAAADgAAAQAAAACtAAAAAAAAAA4AeNpjYIAABSgNAAEQACHHAAAAAAAAAASAAAAAAN8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
        )

    def _create_wad(self) -> bytes:
        return b"IWAD" + b"\x00" * 8

    def _create_xar(self) -> bytes:
        import hashlib
        import zlib

        heap_data = b"Hello, World!\n"
        toc_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b"<xar>\n"
            b"  <toc>\n"
            b'    <checksum style="sha1">\n'
            b"      <offset>0</offset>\n"
            b"      <size>20</size>\n"
            b"    </checksum>\n"
            b'    <file id="1">\n'
            b"      <name>sample.txt</name>\n"
            b"      <type>file</type>\n"
            b"      <data>\n"
            b"        <length>14</length>\n"
            b"        <offset>20</offset>\n"
            b"        <size>14</size>\n"
            b'        <checksum style="sha1">'
            + hashlib.sha1(heap_data).hexdigest().encode("ascii")
            + b"</checksum>\n"
            b"      </data>\n"
            b"    </file>\n"
            b"  </toc>\n"
            b"</xar>"
        )
        toc_comp = zlib.compress(toc_xml)
        # Apple xar specification: checksum of the compressed TOC bytes written to stream
        toc_comp_sha1 = hashlib.sha1(toc_comp).digest()
        xar_hdr = b"xar!\x00\x1c\x00\x01" + struct.pack(
            ">QQI", len(toc_comp), len(toc_xml), 1
        )
        return xar_hdr + toc_comp + toc_comp_sha1 + heap_data

    def _create_z(self) -> bytes:
        return b"\x1f\x9d" + b"\x00" * 20
