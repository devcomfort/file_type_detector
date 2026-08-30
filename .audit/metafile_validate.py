"""Validate EMF/WMF fixtures through LibreOffice Draw import/export."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", choices=("sample-emf", "sample-wmf"), required=True)
    args = parser.parse_args()
    ext = args.id.removeprefix("sample-")
    source = ROOT / "tests" / "fixtures" / f"sample.{ext}"
    data = source.read_bytes()
    if ext == "emf":
        import struct

        assert len(data) == 160
        assert struct.unpack_from("<II", data, 0) == (1, 108)
        assert struct.unpack_from("<I", data, 48)[0] == len(data)
        assert struct.unpack_from("<I", data, 52)[0] == 4
        assert struct.unpack_from("<II", data, 124) == (54, 16)
        assert struct.unpack_from("<II", data, 140) == (14, 20)
    else:
        import struct

        assert struct.unpack_from("<HHH", data, 0) == (1, 9, 0x0300)
        assert struct.unpack_from("<H", data, 6)[0] * 2 == len(data)
        assert struct.unpack_from("<H", data, 12)[0] == 5
        assert struct.unpack_from("<I", data, 18)[0] == 5
        assert struct.unpack_from("<I", data, 28)[0] == 5
    with tempfile.TemporaryDirectory(prefix="metafile-verify-") as output:
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output,
                str(source),
            ],
            check=True,
            capture_output=True,
        )
        pdf = Path(output) / "sample.pdf"
        if not pdf.is_file() or pdf.stat().st_size == 0:
            raise SystemExit("LibreOffice produced no PDF output")
    print(f"{args.id}: LibreOffice Draw import/export passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
