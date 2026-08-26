"""Regenerate flagged fixtures from current deterministic generators."""

import hashlib
import json
import os
import sys

ROOT = "/mnt/workspace/projects/file_type_detector-backend-conformance"
sys.path.insert(0, ROOT)

from scripts.generators.archives import ArchiveGenerator  # noqa: E402
from scripts.generators.data_formats import DataFormatGenerator  # noqa: E402

inv_path = os.path.join(ROOT, "tests/truth/backend_inventory.json")
cand_path = os.path.join(ROOT, "tests/truth/backend_inventory_candidates.json")
inv = json.load(open(inv_path))
cand = json.load(open(cand_path))
records_by_id = {r["id"]: r for r in inv["records"]}

archives = ArchiveGenerator()
datafmt = DataFormatGenerator()

REGEN = {
    "sample-zip": ("zip", archives),
    "sample-gz": ("gz", archives),
    "sample-pcap": ("pcap", datafmt),
}
for rid, (ext, gen_obj) in REGEN.items():
    rec = records_by_id.get(rid)
    if not rec:
        print(f"{rid}: not in inventory, skipped")
        continue
    data = gen_obj.generate(ext)
    fixture_path = os.path.join(ROOT, rec["fixture"])
    with open(fixture_path, "wb") as f:
        f.write(data)
    new_sha = hashlib.sha256(data).hexdigest()

    for doc in (inv, cand):
        for r in doc["records"]:
            if r["id"] == rid:
                old = r["sha256"][:12]
                r["sha256"] = new_sha

    print(f"{rid}: {len(data)}B sha {old}→{new_sha[:12]}")

json.dump(inv, open(inv_path, "w"), indent=1)
json.dump(cand, open(cand_path, "w"), indent=1)

# Final verification: all authoritative records match their checksums
ok = all(
    hashlib.sha256(open(os.path.join(ROOT, r["fixture"]), "rb").read()).hexdigest()
    == r["sha256"]
    for r in inv["records"]
)
print(f"all checksums verified: {'PASS' if ok else 'FAIL'}")
print(f"total authoritative: {len(inv['records'])}")
