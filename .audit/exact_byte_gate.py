"""Exact-byte gate: verify generator output == committed fixture for all
Tier1 (exact-byte) authoritative records. Fails on any mismatch.

Also validates that source_manifest.json sha256 matches inventory sha256.
"""

import hashlib
import json
import os
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

failures = []

# Load tracked data
inv = json.load(open(os.path.join(ROOT, "tests/truth/backend_inventory.json")))
manifest = json.load(open(os.path.join(ROOT, "tests/truth/source_manifest.json")))

# --- Gate 1: inventory sha256 == actual file bytes ---
for r in inv["records"]:
    fixture_path = os.path.join(ROOT, r["fixture"])
    actual = hashlib.sha256(open(fixture_path, "rb").read()).hexdigest()
    if actual != r["sha256"]:
        failures.append(
            f"{r['id']}: inventory sha256 mismatch "
            f"(inventory={r['sha256'][:12]}, actual={actual[:12]})"
        )

# --- Gate 2: manifest sha256 == inventory sha256 ---
for rid in inv_ids if False else [r["id"] for r in inv["records"]]:
    mf = manifest["fixtures"].get(rid)
    rec = next(r for r in inv["records"] if r["id"] == rid)
    if mf is None:
        failures.append(f"{rid}: missing from source_manifest")
    elif mf["sha256"] != rec["sha256"]:
        failures.append(
            f"{rid}: manifest sha256 stale "
            f"(manifest={mf['sha256'][:12]}, inventory={rec['sha256'][:12]})"
        )

# --- Gate 3: Tier1 exact-byte — generator output == committed fixture ---
from scripts.generators.certificates import CertificateGenerator  # noqa: E402
from scripts.generators.archives import ArchiveGenerator  # noqa: E402
from scripts.generators.data_formats import DataFormatGenerator  # noqa: E402

generators = {}
for cls in (CertificateGenerator, ArchiveGenerator, DataFormatGenerator):
    inst = cls()
    for ext in inst.extensions:
        try:
            generators[ext] = inst.generate(ext)
        except Exception:
            pass

TIER1_RECORDS = [
    r
    for r in inv["records"]
    if (r.get("source_integrity") or {}).get("tier") == "exact-byte"
]

for r in TIER1_RECORDS:
    rid = r["id"]
    ext = r["probe_extension"].lstrip(".")
    gen_output = generators.get(ext)
    if gen_output is None:
        failures.append(f"{rid}: no generator output for .{ext} (Tier1)")
        continue
    disk = open(os.path.join(ROOT, r["fixture"]), "rb").read()
    if gen_output != disk:
        failures.append(
            f"{rid}: Tier1 exact-byte MISMATCH "
            f"(gen={len(gen_output)}B/{hashlib.sha256(gen_output).hexdigest()[:12]}, "
            f"disk={len(disk)}B/{hashlib.sha256(disk).hexdigest()[:12]})"
        )

# --- Report ---
if failures:
    print("EXACT-BYTE GATE FAILED:", file=sys.stderr)
    for f in failures:
        print(f"  {f}", file=sys.stderr)
    sys.exit(1)
else:
    tier1_count = len(TIER1_RECORDS)
    total = len(inv["records"])
    print(
        f"exact-byte gate PASSED: {total} checksums verified, {tier1_count} Tier1 byte-exact"
    )
