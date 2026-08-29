"""Exact-byte gate: verify generator output == committed fixture for all
Tier1 (exact-byte) authoritative records. Fails on any mismatch.

Also validates that source_manifest.json sha256 matches inventory sha256.
"""

import hashlib
import json
from pathlib import Path


_PROJECT_ROOT = Path(__file__).parents[2]
sys_path = str(_PROJECT_ROOT)
if sys_path not in __import__("sys").path:
    import sys

    sys.path.insert(0, sys_path)

from scripts.generators.certificates import CertificateGenerator  # noqa: E402
from scripts.generators.archives import ArchiveGenerator  # noqa: E402
from scripts.generators.data_formats import DataFormatGenerator  # noqa: E402
from scripts.generators.code_formats import CodeFormatGenerator  # noqa: E402
from scripts.generators.documents import DocumentGenerator  # noqa: E402
_TIER2 = {"sample-7z", "sample-dxf", "sample-stl"}


def _inv():
    return json.load(open(_PROJECT_ROOT / "tests/truth/backend_inventory.json"))


def _manifest():
    return json.load(open(_PROJECT_ROOT / "tests/truth/source_manifest.json"))


def _generators():
    gens = {}

    for cls in (
        CertificateGenerator,
        ArchiveGenerator,
        DataFormatGenerator,
        CodeFormatGenerator,
        DocumentGenerator,
    ):
        inst = cls()
        for ext in inst.extensions:
            try:
                gens[ext] = inst.generate(ext)
            except Exception:
                pass
    return gens


# Q. Does every authoritative record's fixture bytes match its inventory sha256?
def test_inventory_sha256_matches_fixture_bytes():
    inv = _inv()
    for r in inv["records"]:
        fp = _PROJECT_ROOT / r["fixture"]
        actual = hashlib.sha256(fp.read_bytes()).hexdigest()
        assert actual == r["sha256"], (
            f"{r['id']}: inventory sha256 mismatch "
            f"(inventory={r['sha256'][:12]}, actual={actual[:12]})"
        )


# Q. Does the source manifest agree with the inventory on sha256?
def test_manifest_sha256_consistent_with_inventory():
    manifest = _manifest()
    inv = _inv()
    for r in inv["records"]:
        mf = manifest["fixtures"].get(r["id"])
        assert mf is not None, f"{r['id']}: missing from source_manifest"
        assert mf["sha256"] == r["sha256"], (
            f"{r['id']}: manifest sha256 stale "
            f"(manifest={mf['sha256'][:12]}, inventory={r['sha256'][:12]})"
        )


# Q. Does Tier1 generator output exactly reproduce committed fixture bytes?
def test_tier1_exact_byte_reproduction():
    gens = _generators()
    inv = _inv()
    tier1 = [
        r
        for r in inv["records"]
        if (r.get("source_integrity") or {}).get("tier") == "exact-byte"
    ]
    assert len(tier1) > 0, "no Tier1 records found"

    for r in tier1:
        ext = r["probe_extension"].lstrip(".")
        gen_output = gens.get(ext)
        assert gen_output is not None, f"{r['id']}: no generator for .{ext}"
        disk = (_PROJECT_ROOT / r["fixture"]).read_bytes()
        assert gen_output == disk, (
            f"{r['id']}: Tier1 exact-byte MISMATCH "
            f"(gen={len(gen_output)}B, disk={len(disk)}B)"
        )


# Q. Does the Illustrator-marked AI candidate reproduce its committed bytes?
def test_ai_candidate_exact_byte_reproduction():
    generated = DocumentGenerator().generate("ai")
    committed = (_PROJECT_ROOT / "tests/fixtures/sample.ai").read_bytes()
    assert generated == committed


# Q. Does sample-gzip have .gzip in GT extensions (probe ∈ GT invariant)?
def test_sample_gzip_probe_in_gt_extensions():
    inv = _inv()
    r = next((x for x in inv["records"] if x["id"] == "sample-gzip"), None)
    if r and r["ground_truth_review"]["status"] == "verified":
        assert r["probe_extension"] in r["ground_truth"]["extensions"]
