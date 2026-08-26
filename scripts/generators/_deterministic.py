"""Deterministic helpers for fixture generators.

Timestamps embedded by stdlib writers are pinned so generated fixtures are
byte-reproducible across runs (required by the exact-byte gate).
"""

from __future__ import annotations

import gzip
import zipfile

# Arbitrary but constant DOS timestamp for zip entries.
FIXED_ZIP_DATE_TIME = (2026, 1, 1, 0, 0, 0)
# Unix epoch 0 for gzip mtime.
FIXED_GZIP_MTIME = 0


def write_zip_str(
    zf: zipfile.ZipFile,
    name: str,
    data: str | bytes,
    compress_type: int = zipfile.ZIP_DEFLATED,
) -> None:
    """Write a zip entry with a fixed timestamp.

    ``ZipFile.writestr(str, ...)`` stamps ``time.localtime(time.time())``
    into the entry header, which breaks byte reproducibility. This helper
    supplies an explicit fixed ``ZipInfo`` instead.
    """
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_DATE_TIME)
    info.compress_type = compress_type
    if isinstance(data, str):
        data = data.encode("utf-8")
    zf.writestr(info, data, compress_type=compress_type)


def gzip_compress_det(data: bytes) -> bytes:
    """gzip-compress with a fixed mtime so output is byte-stable."""
    buf_io = __import__("io").BytesIO()
    with gzip.GzipFile(fileobj=buf_io, mode="wb", mtime=FIXED_GZIP_MTIME) as gz:
        gz.write(data)
    return buf_io.getvalue()
