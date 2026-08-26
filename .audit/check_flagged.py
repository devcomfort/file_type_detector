"""Check if flagged records' committed fixtures match current generator output."""

import hashlib
import json
import sys

sys.path.insert(0, ".")
inv = json.load(open("tests/truth/backend_inventory.json"))

from scripts.generators.images import ImageGenerator  # noqa: E402
from scripts.generators.archives import ArchiveGenerator  # noqa: E402
from scripts.generators.data_formats import DataFormatGenerator  # noqa: E402

generators = {}
for cls in (ImageGenerator, ArchiveGenerator, DataFormatGenerator):
    inst = cls()
    for ext in inst.extensions:
        try:
            generators[ext] = inst.generate(ext)
        except Exception:
            pass

for r in inv["records"]:
    rid = r["id"]
    if rid not in (
        "sample-avif",
        "sample-zip",
        "sample-parquet",
        "sample-gz",
        "sample-pcap",
    ):
        continue
    ext = r["probe_extension"].lstrip(".")
    gen = generators.get(ext)
    if gen is None:
        print(f"{rid}: no generator for .{ext}")
        continue
    disk = open(r["fixture"], "rb").read()
    print(f"{rid}: gen={len(gen)}B disk={len(disk)}B match={gen == disk}")
