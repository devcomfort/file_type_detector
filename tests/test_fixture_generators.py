"""Regression tests for portable fixture generation."""

from pathlib import Path

from scripts.generators.__main__ import write_sources_manifest
from scripts.generators.base import BaseGenerator

_CASE_VARIANT_EXTENSIONS = ["CBL", "COB", "CPY", "F90", "P", "R", "S"]
_EXPECTED_FILENAMES = [
    "sample.uppercase.CBL",
    "sample.uppercase.COB",
    "sample.uppercase.CPY",
    "sample.uppercase.F90",
    "sample.uppercase.P",
    "sample.uppercase.R",
    "sample.uppercase.S",
]


class _CaseVariantGenerator(BaseGenerator):
    @property
    def extensions(self) -> list[str]:
        return _CASE_VARIANT_EXTENSIONS

    def generate(self, ext: str) -> bytes:
        return ext.encode("ascii")


# Q. Does the shared generator path preserve case variants on every supported OS?
def test_generator_creates_portable_case_variant_filenames(tmp_path: Path) -> None:
    generator = _CaseVariantGenerator()
    created = [
        generator.create_fixture(tmp_path, ext, force=True)
        for ext in generator.extensions
    ]

    assert all(path is not None for path in created)
    filenames = [path.name for path in created if path is not None]
    assert filenames == _EXPECTED_FILENAMES
    assert len({filename.casefold() for filename in filenames}) == len(filenames)


# Q. Does SOURCES.md retain generated case variants as registered fixtures?
def test_sources_manifest_recognizes_portable_case_variants(tmp_path: Path) -> None:
    for filename in _EXPECTED_FILENAMES:
        (tmp_path / filename).write_bytes(b"fixture")

    write_sources_manifest(tmp_path)

    manifest = (tmp_path / "SOURCES.md").read_text(encoding="utf-8")
    assert "## Discovered fixtures (no registered generator)" not in manifest
    for filename in _EXPECTED_FILENAMES:
        assert f"`{filename}`" in manifest


# Q. Do rpm, snap, and xar generators produce spec-compliant valid archives (pure Python verification)?
def test_spec_compliant_archive_generators(tmp_path):
    import gzip
    import zlib
    import hashlib
    import struct
    import shutil
    import subprocess
    from scripts.generators.archives import ArchiveGenerator

    gen = ArchiveGenerator()

    # 1. RPM verification (Lead + CPIO payload structural parse)
    rpm_bytes = gen.generate("rpm")
    assert rpm_bytes.startswith(b"\xed\xab\xee\xdb")
    gz_idx = rpm_bytes.index(b"\x1f\x8b")
    cpio_raw = gzip.decompress(rpm_bytes[gz_idx:])

    # Pure-Python newc CPIO structural validation
    assert len(cpio_raw) >= 110
    assert cpio_raw[:6] == b"070701"
    namesize = int(cpio_raw[94:102], 16)
    filesize = int(cpio_raw[54:62], 16)
    filename = cpio_raw[110 : 110 + namesize].rstrip(b"\x00")
    assert filename == b"sample.txt"
    filedata_pos = 110 + namesize + ((4 - (110 + namesize) % 4) % 4)
    filedata = cpio_raw[filedata_pos : filedata_pos + filesize]
    assert filedata == b"Hello, World!\n"

    # Optional: if system cpio binary is present, also execute CLI extraction
    if shutil.which("cpio"):
        res = subprocess.run(
            ["cpio", "-t"],
            input=cpio_raw,
            capture_output=True,
            check=True,
        )
        assert b"sample.txt" in res.stdout or b"sample.txt" in res.stderr

    # 2. Snap verification (SquashFS 4.0 superblock parse + optional unsquashfs)
    snap_bytes = gen.generate("snap")
    assert snap_bytes.startswith(b"hsqs")
    assert len(snap_bytes) >= 96
    s_magic, inodes, mkfs_time, block_size, fragments = struct.unpack(
        "<IIIII", snap_bytes[0:20]
    )
    compression, block_log, flags, no_ids, s_major, s_minor = struct.unpack(
        "<HHHHHH", snap_bytes[20:32]
    )
    assert s_magic == 0x73717368
    assert s_major == 4 and s_minor == 0
    assert compression == 1  # gzip

    if shutil.which("unsquashfs"):
        snap_file = tmp_path / "test.snap"
        snap_file.write_bytes(snap_bytes)
        out_dir = tmp_path / "extracted"
        subprocess.run(
            ["unsquashfs", "-d", str(out_dir), str(snap_file)],
            capture_output=True,
            check=True,
        )
        assert (out_dir / "sample.txt").read_bytes() == b"Hello, World!\n"

    # 3. XAR verification (TOC decompression and compressed-TOC SHA1 verification)
    xar_bytes = gen.generate("xar")
    assert xar_bytes.startswith(b"xar!")
    magic, hdr_size, version, toc_comp_len, toc_uncomp_len, cksum_alg = struct.unpack(
        ">4sHHQQI", xar_bytes[:28]
    )
    assert cksum_alg == 1
    comp_toc = xar_bytes[28 : 28 + toc_comp_len]
    uncomp_toc = zlib.decompress(comp_toc)
    assert len(uncomp_toc) == toc_uncomp_len
    heap = xar_bytes[28 + toc_comp_len :]
    toc_checksum_in_heap = heap[:20]
    # Apple xar verifies checksum over the compressed TOC stream
    assert hashlib.sha1(comp_toc).digest() == toc_checksum_in_heap


# Q. Does the registered zlibstream dispatch reproduce its committed fixture?
def test_zlibstream_dispatch_matches_fixture() -> None:
    import hashlib
    from scripts.generators.archives import ArchiveGenerator

    generated = ArchiveGenerator().generate("zlibstream")
    committed = (Path(__file__).parent / "fixtures" / "sample.zlibstream").read_bytes()
    assert generated == committed
    assert (
        hashlib.sha256(generated).hexdigest()
        == "89ec7a2ae631b811b677373421fc2946e0beea5e09c0e37fbb3e99dce57e146e"
    )


# Q. Do archive extension, source, and dispatch registries stay aligned?
def test_archive_registry_keys_are_complete() -> None:
    from scripts.generators.archives import ArchiveGenerator

    generator = ArchiveGenerator()
    assert set(generator.extensions) == set(generator.sources)
    for extension in generator.extensions:
        generated = generator.generate(extension)
        assert isinstance(generated, bytes)
        assert generated
