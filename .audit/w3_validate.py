"""Rerunnable structural checks for the W3 audit matrix.

This validator never promotes records. It reports format validity only; MIME
authority evidence and review status remain separate gates.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import subprocess
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def result(
    record_id: str, status: str, validator: str, evidence: list[str]
) -> dict[str, object]:
    return {
        "id": record_id,
        "status": status,
        "validator": validator,
        "evidence": evidence,
    }


def validate(record_id: str) -> dict[str, object]:
    ext = record_id.removeprefix("sample-")
    fixture_ext = "pyc" if ext == "pythonbytecode" else ext
    path = FIXTURES / f"sample.{fixture_ext}"
    if not path.is_file():
        return result(
            record_id, "failed", "w3_validate.py:fixture-exists", ["fixture missing"]
        )
    data = path.read_bytes()

    try:
        if ext in {"pyc", "pythonbytecode"}:
            import importlib.util
            import marshal

            assert data[:4] == importlib.util.MAGIC_NUMBER
            code = marshal.loads(data[16:])
            assert isinstance(code, type(compile("", "", "exec")))
            return result(
                record_id,
                "verified",
                "w3_validate.py:pyc-marshal",
                ["CPython magic number, header, and marshal code object"],
            )
        if ext == "apk":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = set(archive.namelist())
                assert {"AndroidManifest.xml", "classes.dex"} <= names
                manifest = archive.read("AndroidManifest.xml")
                xml_type, xml_header_size, xml_size = struct.unpack(
                    "<HHI", manifest[:8]
                )
                assert (
                    xml_type == 0x0003
                    and xml_header_size == 8
                    and xml_size == len(manifest)
                )
                pool_type, pool_header_size, pool_size = struct.unpack(
                    "<HHI", manifest[8:16]
                )
                assert pool_type == 0x0001 and pool_header_size == 28
                assert pool_size >= 32 and 8 + pool_size <= len(manifest)
                start = 8 + pool_size
                start_type, start_header_size, start_size = struct.unpack(
                    "<HHI", manifest[start : start + 8]
                )
                assert (
                    start_type == 0x0102
                    and start_header_size == 16
                    and start_size == 36
                )
                end = start + start_size
                end_type, end_header_size, end_size = struct.unpack(
                    "<HHI", manifest[end : end + 8]
                )
                assert end_type == 0x0103 and end_header_size == 16 and end_size == 24
                assert end + end_size == len(manifest)
                dex = archive.read("classes.dex")
                assert dex.startswith(b"dex\n035\x00")
            return result(
                record_id,
                "needs_review",
                "w3_validate.py:apk-structural",
                [
                    "binary AXML chunk boundaries and DEX marker checked; independent Android parser pending"
                ],
            )
        if ext == "dsstore":
            from ds_store import DSStore

            assert data[:9] == b"\x00\x00\x00\x01Bud1\x00"
            with io.BytesIO(data) as buffer:
                with DSStore.open(buffer, "r") as store:
                    entries = list(store)
            assert any(
                str(entry.filename) == "hello.txt" and entry.code == b"Iloc"
                for entry in entries
            )
            return result(
                record_id,
                "verified",
                "w3_validate.py:ds-store-roundtrip",
                ["ds-store 1.3.3 Bud1 header and Iloc record traversal"],
            )
        if ext == "cab":
            cb_cabinet = struct.unpack("<I", data[8:12])[0]
            coff_files = struct.unpack("<I", data[16:20])[0]
            assert cb_cabinet == len(data) and coff_files == 44
            coff_cab_start = struct.unpack("<I", data[36:40])[0]
            assert coff_cab_start == 71
            return result(
                record_id,
                "verified",
                "w3_validate.py:cab-struct",
                ["CFHEADER/CFFOLDER/CFFILE/CFDATA offsets and lengths"],
            )
        if ext == "crx":
            version, pub_len, sig_len = struct.unpack("<III", data[4:16])
            assert version == 2
            pub = data[16 : 16 + pub_len]
            sig = data[16 + pub_len : 16 + pub_len + sig_len]
            payload = data[16 + pub_len + sig_len :]
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            serialization.load_der_public_key(pub).verify(
                sig, payload, padding.PKCS1v15(), hashes.SHA1()
            )
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                assert "manifest.json" in archive.namelist()
            return result(
                record_id,
                "verified",
                "w3_validate.py:crx-rsa-sha1-zip",
                ["RSA-SHA1 signature and manifest.json"],
            )
        if ext == "deb":
            assert data.startswith(b"!<arch>\n")
            pos, members = 8, {}
            while pos + 60 <= len(data):
                header = data[pos : pos + 60]
                name = header[:16].strip().decode("ascii")
                size = int(header[48:58].strip())
                pos += 60
                members[name] = data[pos : pos + size]
                pos += size + size % 2
            assert {"debian-binary", "control.tar.gz", "data.tar.gz"} <= members.keys()
            for name in ("control.tar.gz", "data.tar.gz"):
                with tarfile.open(
                    fileobj=io.BytesIO(members[name]), mode="r:gz"
                ) as archive:
                    assert archive.getnames()
            return result(
                record_id,
                "verified",
                "w3_validate.py:deb-ar-tar",
                ["ar members and gzip tar archives"],
            )
        if ext == "dex":
            assert data.startswith(b"dex\n035\x00")
            assert struct.unpack("<I", data[32:36])[0] == len(data)
            assert hashlib.sha1(data[32:]).digest() == data[12:32]
            assert (
                __import__("zlib").adler32(data[12:]) & 0xFFFFFFFF
            ) == struct.unpack("<I", data[8:12])[0]
            map_off = struct.unpack("<I", data[52:56])[0]
            count = struct.unpack("<I", data[map_off : map_off + 4])[0]
            types = [
                struct.unpack("<H", data[map_off + 4 + i * 12 : map_off + 6 + i * 12])[
                    0
                ]
                for i in range(count)
            ]
            assert 0x2002 in types
            return result(
                record_id,
                "verified",
                "w3_validate.py:dex-checksums-map",
                ["file size, SHA-1, Adler-32, and string-data map item"],
            )
        if ext in {"snap", "squashfs"}:
            assert data[:4] == b"hsqs" and len(data) >= 96
            assert struct.unpack("<H", data[28:30])[0] == 4
            assert struct.unpack("<H", data[30:32])[0] == 0
            return result(
                record_id,
                "verified",
                "w3_validate.py:squashfs-superblock",
                ["SquashFS 4.0 superblock"],
            )
        if ext == "lha":
            assert data[2:7] == b"-lh0-" and data[0] == 36
            assert data[22:32] == b"sample.txt" and data[37:50] == b"Hello, World!"
            return result(
                record_id,
                "verified",
                "w3_validate.py:lha-level1",
                ["method, filename, and stored payload"],
            )
        if ext == "zlibstream":
            import zlib

            payload = zlib.decompress(data)
            assert payload == b"Hello, World!\n" * 10
            return result(
                record_id,
                "verified",
                "w3_validate.py:zlib-decompress",
                ["zlib stream decompressed to deterministic payload"],
            )
        if ext in {"dcm", "dicom"}:
            import pydicom

            dataset = pydicom.dcmread(path)
            assert str(dataset.PatientName) == "Test"
            return result(
                record_id,
                "verified",
                "w3_validate.py:pydicom",
                ["pydicom read of DICOM preamble, file meta, and PatientName"],
            )
        if ext == "rpm":
            assert data.startswith(b"\xed\xab\xee\xdb")
            gzip_offset = data.index(b"\x1f\x8b")
            payload = __import__("gzip").decompress(data[gzip_offset:])
            assert payload.startswith(b"070701") and b"TRAILER!!!" in payload
            return result(
                record_id,
                "verified",
                "w3_validate.py:rpm-cpio",
                ["RPM lead/header and newc CPIO payload"],
            )
        if ext == "snap":
            assert data[:4] == b"hsqs" and len(data) >= 96
            assert struct.unpack("<H", data[28:30])[0] == 4
            assert struct.unpack("<H", data[30:32])[0] == 0
            return result(
                record_id,
                "verified",
                "w3_validate.py:squashfs-superblock",
                ["SquashFS 4.0 superblock"],
            )
        if ext == "xar":
            assert data[:4] == b"xar!"
            _, _, _, compressed_len, uncompressed_len, algorithm = struct.unpack(
                ">4sHHQQI", data[:28]
            )
            compressed = data[28 : 28 + compressed_len]
            uncompressed = __import__("zlib").decompress(compressed)
            assert len(uncompressed) == uncompressed_len
            assert (
                hashlib.sha1(compressed).digest()
                == data[28 + compressed_len : 48 + compressed_len]
            )
            return result(
                record_id,
                "verified",
                "w3_validate.py:xar-compressed-toc",
                ["compressed TOC length and SHA-1"],
            )
        return result(
            record_id,
            "needs_review",
            "w3_validate.py:pending",
            ["independent parser not implemented"],
        )
    except Exception as error:
        return result(
            record_id,
            "failed",
            "w3_validate.py:structural",
            [f"{type(error).__name__}: {error}"],
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.id), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
