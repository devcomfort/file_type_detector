"""Archive format generators."""

import bz2
import gzip
import struct
import tarfile
import zipfile
from io import BytesIO

import lz4.frame
import zstandard

from .base import BaseGenerator
from . import register


@register
class ArchiveGenerator(BaseGenerator):
    """Generates minimal valid archive files."""

    @property
    def extensions(self) -> list[str]:
        return [
            "zip", "tar", "gz", "tgz", "bz2", "tbz2", "xz", "lz", "lz4",
            "zst", "7z", "xpi", "jar", "apk", "gzip", "nupkg", "maff",
            "tar.gz", "tar.bz2", "rz",
            "arc", "lha", "lrz", "lzh", "pkg", "rpm", "snap", "wad", "xar", "z",
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
            zf.writestr("hello.txt", "Hello, World!\n")
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
        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as f:
            f.write(b"Hello, World!\n")
        return buf.getvalue()

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
            zf.writestr("sample.nuspec", '<?xml version="1.0"?><package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"><metadata><id>Sample</id><version>1.0.0</version><description>Sample package</description></metadata></package>')
        return buf.getvalue()

    def _create_maff(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", "<html><body>Sample</body></html>")
        return buf.getvalue()

    def _create_rz(self) -> bytes:
        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
            f.write(b"Hello, World!\n")
        return buf.getvalue()

    def _create_arc(self) -> bytes:
        return b"\x1a" + b"\x00" * 20

    def _create_lha(self) -> bytes:
        return b"-lh0-" + b"\x00" * 20

    def _create_lrz(self) -> bytes:
        return b"LRZI" + b"\x00" * 20

    def _create_lzh(self) -> bytes:
        return b"-lh0-" + b"\x00" * 20

    def _create_pkg(self) -> bytes:
        return b"xar!\x00\x01" + struct.pack(">I", 28) + b"\x00" * 16

    def _create_rpm(self) -> bytes:
        return b"\xed\xab\xee\xdb" + b"\x00" * 20

    def _create_snap(self) -> bytes:
        return b"hsqs" + b"\x00" * 20

    def _create_wad(self) -> bytes:
        return b"IWAD" + b"\x00" * 8

    def _create_xar(self) -> bytes:
        return b"xar!\x00\x01" + struct.pack(">I", 28) + b"\x00" * 16

    def _create_z(self) -> bytes:
        return b"\x1f\x9d" + b"\x00" * 20
