"""DEPRECATED: This standalone download script is no longer the canonical path.

Use ``scripts/generators`` instead:

    rye run python -m scripts.generators --all --sources

The download-backed fixtures have been integrated into the generators registry
at ``scripts/generators/downloads.py``.  Run the command above to regenerate
all fixtures — including downloaded ones — in a single workflow.

This module is kept for reference only and will be removed in a future release.
---

Usage (legacy):
    python scripts/download_fixtures.py [--force]
"""

import argparse
import urllib.request
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"

# Sources with permissive licenses (Apache 2.0, MIT, etc.)
SOURCES = {
    # Apache POI test data (Apache License 2.0)
    # https://github.com/apache/poi/tree/master/test-data
    "sample.ppt": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/document/pptWithImages.ppt",
        "Apache POI (Apache 2.0)",
    ),
    "sample.pptx": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/slideshow/withImages.pptx",
        "Apache POI (Apache 2.0)",
    ),
    "sample.doc": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/document/Word.doc",
        "Apache POI (Apache 2.0)",
    ),
    "sample.docx": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/document/Word.docx",
        "Apache POI (Apache 2.0)",
    ),
    "sample.xls": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/spreadsheet/35188.xls",
        "Apache POI (Apache 2.0)",
    ),
    "sample.xlsx": (
        "https://raw.githubusercontent.com/apache/poi/master/test-data/spreadsheet/59689.xlsx",
        "Apache POI (Apache 2.0)",
    ),
    # hwp-rs test fixtures (Apache License 2.0)
    # https://github.com/hahnlee/hwp-rs/tree/main/tests/data
    "sample.hwp": (
        "https://raw.githubusercontent.com/hahnlee/hwp-rs/main/tests/data/sample.hwp",
        "hwp-rs (Apache 2.0)",
    ),
    # LibreOffice test files (MPL 2.0)
    # https://cgit.freedesktop.org/libreoffice/core/tree/oox/qa/test-documents
    "sample.odt": (
        "https://cgit.freedesktop.org/libreoffice/core/plain/odfqa/odt/bug63148-1.odt?h=libreoffice-25-2-0-3",
        "LibreOffice (MPL 2.0)",
    ),
    "sample.ods": (
        "https://cgit.freedesktop.org/libreoffice/core/plain/odfqa/ods/bug104848.ods?h=libreoffice-25-2-0-3",
        "LibreOffice (MPL 2.0)",
    ),
    "sample.odp": (
        "https://cgit.freedesktop.org/libreoffice/core/plain/odfqa/odp/bug119105.odp?h=libreoffice-25-2-0-3",
        "LibreOffice (MPL 2.0)",
    ),
    # SQLite test database (Public Domain)
    # https://www.sqlite.org/src
    "sample.sqlite": (
        "https://www.sqlite.org/src/raw?name=test/lock.test&ln=1",
        "SQLite (Public Domain)",
    ),
    # Sample media files from various open-source projects
    "sample.mp3": (
        "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
        "UIC CS101 (Educational)",
    ),
    "sample.wav": (
        "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
        "UIC CS101 (Educational)",
    ),
    # Sample images from Wikimedia Commons (Public Domain)
    "sample.png": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/100px-PNG_transparency_demonstration_1.png",
        "Wikimedia Commons (Public Domain)",
    ),
    "sample.jpg": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Sunflower_from_Silesia.jpg/100px-Sunflower_from_Silesia.jpg",
        "Wikimedia Commons (Public Domain)",
    ),
    "sample.gif": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/LPD_brooke_castle.gif/100px-LPD_brooke_castle.gif",
        "Wikimedia Commons (Public Domain)",
    ),
    "sample.webp": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Google_Chrome_Logo_2011.svg/100px-Google_Chrome_Logo_2011.svg.png.webp",
        "Wikimedia Commons (Public Domain)",
    ),
    "sample.tiff": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/100px-PNG_transparency_demonstration_1.png.tiff",
        "Wikimedia Commons (Public Domain)",
    ),
    "sample.bmp": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/100px-PNG_transparency_demonstration_1.png.bmp",
        "Wikimedia Commons (Public Domain)",
    ),
    "sample.ico": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/100px-PNG_transparency_demonstration_1.png.ico",
        "Wikimedia Commons (Public Domain)",
    ),
    "sample.svg": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Google_Chrome_Logo_2011.svg/100px-Google_Chrome_Logo_2011.svg.svg",
        "Wikimedia Commons (Public Domain)",
    ),
    # Archive files from various sources
    "sample.zip": (
        "https://github.com/google/magika/archive/refs/heads/main.zip",
        "Magika (Apache 2.0)",
    ),
    "sample.tar.gz": (
        "https://github.com/google/magika/archive/refs/heads/main.tar.gz",
        "Magika (Apache 2.0)",
    ),
    "sample.bz2": (
        "https://github.com/google/magika/archive/refs/heads/main.tar.bz2",
        "Magika (Apache 2.0)",
    ),
    # Font files from Google Fonts (Apache 2.0 / OFL)
    "sample.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf",
        "Google Fonts (OFL 1.1)",
    ),
    "sample.otf": (
        "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.otf",
        "Google Fonts (OFL 1.1)",
    ),
    "sample.woff": (
        "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.woff",
        "Google Fonts (OFL 1.1)",
    ),
    "sample.woff2": (
        "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.woff2",
        "Google Fonts (OFL 1.1)",
    ),
    # Video files from sample-videos.com (Creative Commons)
    "sample.mp4": (
        "https://sample-videos.com/video321/mp4/240/big_buck_bunny_240p_1mb.mp4",
        "Sample Videos (CC)",
    ),
    # Executable files from various sources
    "sample.elf": (
        "https://github.com/unicorn-engine/unicorn/raw/master/tests/regress/x86_64/exit.bin",
        "Unicorn Engine (LGPL 2.1)",
    ),
}


def download_file(url: str, path: Path, force: bool = False) -> bool:
    """Download a file from URL to path.

    Parameters
    ----------
    url : str
        Source URL.
    path : Path
        Destination file path.
    force : bool
        Overwrite existing files.

    Returns
    -------
    bool
        True if download succeeded, False otherwise.
    """
    if path.exists() and not force:
        return True

    try:
        print(f"  Downloading {path.name} from {url[:60]}...")
        urllib.request.urlretrieve(url, path)
        size = path.stat().st_size
        print(f"  ✓ {path.name} ({size:,} bytes)")
        return True
    except Exception as e:
        print(f"  ✗ {path.name}: {e}")
        if path.exists():
            path.unlink()
        return False


def main():
    """Download all fixture files."""
    parser = argparse.ArgumentParser(description="Download binary fixture files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Download only fixtures matching this extension (e.g., 'ppt', 'doc')",
    )
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0
    skipped = 0

    for name, (url, source) in sorted(SOURCES.items()):
        # Apply filter if specified
        if args.filter:
            ext = name.split(".")[-1]
            if ext != args.filter:
                continue

        path = FIXTURES_DIR / name
        if path.exists() and not args.force:
            skipped += 1
            continue

        if download_file(url, path, force=args.force):
            success += 1
        else:
            failed += 1

    # Summary
    print()
    print("Download complete:")
    print(f"  ✓ {success} succeeded")
    print(f"  ✗ {failed} failed")
    print(f"  - {skipped} skipped (already exist)")
    print()

    # List all fixtures
    existing = sorted(FIXTURES_DIR.glob("sample.*"))
    print(f"Total fixtures: {len(existing)}")
    for f in existing:
        print(f"  {f.name:20s} ({f.stat().st_size:>10,} bytes)")


if __name__ == "__main__":
    main()
