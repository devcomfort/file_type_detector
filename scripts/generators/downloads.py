"""Download-based fixture generators for binary formats.

These formats cannot be easily created with Python libraries, so we download
small sample files from public repositories.
"""

import urllib.request
from pathlib import Path

from .base import BaseGenerator
from . import register


# Source URLs mapping — each entry maps an extension to a direct download URL
# and the expected size range (for validation).
# All URLs point to raw.githubusercontent.com for reliability.
_DOWNLOAD_SOURCES: dict[str, tuple[str, int]] = {
    # === Archive formats (iamahsanmehmood/sample-files) ===
    "rar": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.rar",
        1_000_000,
    ),
    "cab": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.cab",
        1_000_000,
    ),
    "arj": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.arj",
        1_000_000,
    ),
    "deb": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.deb",
        1_000_000,
    ),
    "msi": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.msi",
        1_000_000,
    ),
    "iso": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.iso",
        1_000_000,
    ),
    "lnk": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.lnk",
        1_000_000,
    ),
    "crx": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.crx",
        1_000_000,
    ),
    "dmg": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/archives/sample.dmg",
        1_000_000,
    ),

    # === Executable formats (iamahsanmehmood/sample-files) ===
    "exe": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/executables/sample.exe",
        1_000_000,
    ),
    "dll": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/executables/sample.dll",
        1_000_000,
    ),

    # === Document formats (iamahsanmehmood/sample-files) ===
    "chm": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/documents/sample.chm",
        1_000_000,
    ),
    "one": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/documents/sample.one",
        1_000_000,
    ),
    "vsd": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/documents/sample.vsd",
        1_000_000,
    ),

    # === CAD formats (iamahsanmehmood/sample-files) ===
    "dwg": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/cad/sample.dwg",
        1_000_000,
    ),

    # === Font formats (iamahsanmehmood/sample-files) ===
    "eot": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/fonts/sample.eot",
        1_000_000,
    ),
    "woff2": (
        "https://raw.githubusercontent.com/iamahsanmehmood/sample-files/main/fonts/sample.woff2",
        1_000_000,
    ),

    # === WebAssembly (h2non/filetype) ===
    "wasm": (
        "https://raw.githubusercontent.com/h2non/filetype/master/fixtures/sample.wasm",
        1_000_000,
    ),

    # === Network capture (wireshark/wireshark) ===
    "pcapng": (
        "https://raw.githubusercontent.com/wireshark/wireshark/master/test/captures/bt_attr.pcapng",
        1_000_000,
    ),

    # === Office documents (Apache POI, Apache License 2.0) ===
    "doc": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/document/Word.doc",
        1_000_000,
    ),
    "docx": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/document/Word.docx",
        1_000_000,
    ),
    "ppt": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/document/pptWithImages.ppt",
        1_000_000,
    ),
    "pptx": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/slideshow/withImages.pptx",
        1_000_000,
    ),
    "xls": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/spreadsheet/35188.xls",
        1_000_000,
    ),
    "xlsx": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/spreadsheet/59689.xlsx",
        1_000_000,
    ),

    # === HWP (hwp-rs, Apache License 2.0) ===
    "hwp": (
        "https://raw.githubusercontent.com/hahnlee/hwp-rs/main/tests/data/sample.hwp",
        5_000_000,
    ),

    # === HWPX (hwp-rs, Apache License 2.0) ===
    "hwpx": (
        "https://raw.githubusercontent.com/hahnlee/hwp-rs/main/tests/data/sample.hwpx",
        5_000_000,
    ),
}


@register
class DownloadGenerator(BaseGenerator):
    """Generates fixtures by downloading sample files from public repositories."""

    @property
    def extensions(self) -> list[str]:
        return list(_DOWNLOAD_SOURCES.keys())

    @property
    def category(self) -> str:
        return "download"

    @property
    def sources(self) -> dict[str, str]:
        return {ext: f"download:{url}" for ext, (url, _) in _DOWNLOAD_SOURCES.items()}

    def generate(self, ext: str) -> bytes:
        if ext not in _DOWNLOAD_SOURCES:
            raise ValueError(f"No download source for .{ext}")
        url, max_size = _DOWNLOAD_SOURCES[ext]
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        if len(data) > max_size:
            raise ValueError(
                f"Downloaded .{ext} is too large: {len(data)} bytes (max: {max_size})"
            )
        return data

    def create_fixture(self, output_dir: Path, ext: str, force: bool = False) -> Path | None:
        path = output_dir / f"sample.{ext}"
        if path.exists() and not force:
            return None
        try:
            content = self.generate(ext)
            path.write_bytes(content)
            return path
        except Exception as e:
            print(f"  Warning: Failed to download .{ext}: {e}")
            return None
