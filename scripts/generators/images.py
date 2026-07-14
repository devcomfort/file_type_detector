"""Image format generators using Pillow."""

import struct
import zlib
from io import BytesIO

from .base import BaseGenerator
from . import register


@register
class ImageGenerator(BaseGenerator):
    """Generates minimal valid image files."""

    @property
    def extensions(self) -> list[str]:
        return [
            "png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "ico",
            "webp", "tga", "icns", "psd", "xcf", "qoi", "jng",
            "avif", "avifs", "jp2", "heic", "heif", "heics", "heifs", "jxl",
        ]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "png": "library:Pillow",
            "jpg": "library:Pillow",
            "jpeg": "library:Pillow",
            "gif": "library:Pillow",
            "bmp": "library:Pillow",
            "tiff": "library:Pillow",
            "tif": "library:Pillow",
            "ico": "library:Pillow",
            "webp": "library:Pillow",
            "tga": "synthetic:TGA header + raw pixel data",
            "icns": "synthetic:icns magic + icon type header",
            "psd": "synthetic:PSD magic bytes",
            "xcf": "synthetic:GIMP XCF magic bytes",
            "qoi": "synthetic:QOI header + raw pixel data",
            "jng": "synthetic:JNG magic bytes",
            "avif": "library:Pillow",
            "avifs": "library:Pillow",
            "jp2": "library:Pillow",
            "heic": "library:Pillow+pillow-heif",
            "heif": "library:Pillow+pillow-heif",
            "heics": "library:Pillow+pillow-heif",
            "heifs": "library:Pillow+pillow-heif",
            "jxl": "library:Pillow",
        }

    @property
    def category(self) -> str:
        return "image"

    def generate(self, ext: str) -> bytes:
        generators = {
            "png": self._create_png,
            "jpg": self._create_jpeg,
            "jpeg": self._create_jpeg,
            "gif": self._create_gif,
            "bmp": self._create_bmp,
            "tiff": self._create_tiff,
            "tif": self._create_tiff,
            "ico": self._create_ico,
            "webp": self._create_webp,
            "tga": self._create_tga,
            "icns": self._create_icns,
            "psd": self._create_psd,
            "xcf": self._create_xcf,
            "qoi": self._create_qoi,
            "jng": self._create_jng,
            "avif": self._create_avif,
            "avifs": self._create_avifs,
            "jp2": self._create_jp2,
            "heic": self._create_heic,
            "heif": self._create_heif,
            "heics": self._create_heics,
            "heifs": self._create_heifs,
            "jxl": self._create_jxl,
        }
        return generators[ext]()

    def _create_png(self) -> bytes:
        def chunk(chunk_type: bytes, data: bytes) -> bytes:
            c = chunk_type + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        sig = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        raw = zlib.compress(b"\x00\xff\x00\x00")
        idat = chunk(b"IDAT", raw)
        iend = chunk(b"IEND", b"")
        return sig + ihdr + idat + iend

    def _create_jpeg(self) -> bytes:
        return (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09"
            b"\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f"
            b"\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20\x22\x2c\x23\x1c\x1c\x28\x37"
            b"\x29\x2c\x30\x31\x34\x34\x34\x1f\x27\x39\x3d\x38\x32\x3c\x2e\x33\x34"
            b"\x32\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00"
            b"\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xc4\x00\xb5"
            b"\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01\x7d"
            b"\x01\x02\x03\x00\x04\x11\x05\x12\x21\x31\x41\x06\x13\x51\x61\x07\x22"
            b"\x71\x14\x32\x81\x91\xa1\x08\x23\x42\xb1\xc1\x15\x52\xd1\xf0\x24\x33"
            b"\x62\x72\x82\x09\x0a\x16\x17\x18\x19\x1a\x25\x26\x27\x28\x29\x2a\x34"
            b"\x35\x36\x37\x38\x39\x3a\x43\x44\x45\x46\x47\x48\x49\x4a\x53\x54\x55"
            b"\x56\x57\x58\x59\x5a\x63\x64\x65\x66\x67\x68\x69\x6a\x73\x74\x75\x76"
            b"\x77\x78\x79\x7a\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96"
            b"\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5"
            b"\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4"
            b"\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1"
            b"\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00"
            b"\x3f\x00\x7b\x40\x03\xff\xd9"
        )

    def _create_gif(self) -> bytes:
        return (
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\x00\x00\x00\x00\x00"
            b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b"
        )

    def _create_bmp(self) -> bytes:
        return (
            b"BM" + struct.pack("<I", 62) + struct.pack("<HH", 0, 0)
            + struct.pack("<I", 62) + struct.pack("<I", 40)
            + struct.pack("<i", 1) + struct.pack("<i", 1)
            + struct.pack("<HH", 1, 24) + struct.pack("<I", 0)
            + struct.pack("<I", 0) + struct.pack("<i", 2835)
            + struct.pack("<i", 2835) + struct.pack("<I", 0)
            + struct.pack("<I", 0) + b"\xff\x00\x00\x00"
        )

    def _create_tiff(self) -> bytes:
        return b"II" + struct.pack("<H", 42) + struct.pack("<I", 8) + struct.pack("<H", 0)

    def _create_ico(self) -> bytes:
        return (
            b"\x00\x00" + struct.pack("<H", 1) + struct.pack("<H", 1)
            + b"\x01\x01\x00\x00" + struct.pack("<H", 1) + struct.pack("<H", 32)
            + struct.pack("<I", 44) + struct.pack("<I", 22)
            + struct.pack("<I", 40) + struct.pack("<i", 1) + struct.pack("<i", 2)
            + struct.pack("<H", 1) + struct.pack("<H", 32)
            + struct.pack("<I", 0) + struct.pack("<I", 0)
            + struct.pack("<i", 0) + struct.pack("<i", 0)
            + struct.pack("<I", 0) + struct.pack("<I", 0)
            + b"\xff\x00\x00\xff" + b"\x00\x00\x00\x00"
        )

    def _create_webp(self) -> bytes:
        vp8 = b"\x9d\x01\x2a\x01\x00\x00" + struct.pack("<HH", 1, 1) + b"\x00"
        return b"RIFF" + struct.pack("<I", 4 + 8 + len(vp8)) + b"WEBPVP8 " + struct.pack("<I", len(vp8)) + vp8

    def _create_tga(self) -> bytes:
        return (
            struct.pack("<BBBBBHHBHH", 0, 0, 2, 0, 0, 0, 0, 0, 0, 0)
            + struct.pack("<HH", 1, 1)
            + struct.pack("<B", 24)
            + struct.pack("<B", 0)
            + b"\xff\x00\x00"
        )

    def _create_icns(self) -> bytes:
        data = b"\x00\x00\x00\x00" * 16
        return b"icns" + struct.pack(">I", 8 + len(data)) + data

    def _create_psd(self) -> bytes:
        return b"8BPS" + struct.pack(">HH", 1, 0) + struct.pack(">IIII", 1, 1, 1, 8)

    def _create_xcf(self) -> bytes:
        return b"gimp xcf " + struct.pack(">I", 0) + struct.pack(">II", 1, 1)

    def _create_qoi(self) -> bytes:
        return (
            b"qoif" + struct.pack(">II", 1, 1) + b"\x00\x00\x00\x00"
            + b"\xfe\xff\x00\x00\x00\x00\x00\x01"
        )

    def _create_jng(self) -> bytes:
        return b"\x8aJNG\r\n\x1a\n" + struct.pack(">I", 0)

    def _create_avif(self) -> bytes:
        from PIL import Image
        buf = BytesIO()
        img = Image.new("RGB", (8, 8), (255, 0, 0))
        img.save(buf, format="AVIF")
        return buf.getvalue()

    def _create_avifs(self) -> bytes:
        return self._create_avif()

    def _create_jp2(self) -> bytes:
        from PIL import Image
        buf = BytesIO()
        img = Image.new("RGB", (8, 8), (255, 0, 0))
        img.save(buf, format="JPEG2000")
        return buf.getvalue()

    def _create_heic(self) -> bytes:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        from PIL import Image
        buf = BytesIO()
        img = Image.new("RGB", (8, 8), (255, 0, 0))
        img.save(buf, format="HEIF")
        return buf.getvalue()

    def _create_heif(self) -> bytes:
        return self._create_heic()

    def _create_heics(self) -> bytes:
        return self._create_heic()

    def _create_heifs(self) -> bytes:
        return self._create_heic()

    def _create_jxl(self) -> bytes:
        from PIL import Image
        buf = BytesIO()
        img = Image.new("RGB", (8, 8), (255, 0, 0))
        img.save(buf, format="JXL")
        return buf.getvalue()
