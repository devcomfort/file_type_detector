"""Regenerate cert fixtures deterministically and update tracked inventory hashes."""

import hashlib
import json
import os
import sys

ROOT = "/mnt/workspace/projects/file_type_detector-backend-conformance"
sys.path.insert(0, ROOT)

from scripts.generators.certificates import CertificateGenerator  # noqa: E402

g = CertificateGenerator()

inv_path = os.path.join(ROOT, "tests/truth/backend_inventory.json")
cand_path = os.path.join(ROOT, "tests/truth/backend_inventory_candidates.json")

inv = json.load(open(inv_path))
cand = json.load(open(cand_path))

records_by_id = {r["id"]: r for r in inv["records"]}

for rid, ext in (("sample-cer", "cer"), ("sample-crt", "crt"), ("sample-der", "der")):
    rec = records_by_id.get(rid)
    if not rec:
        continue
    data = g.generate(ext)
    fixture_path = os.path.join(ROOT, rec["fixture"])
    with open(fixture_path, "wb") as f:
        f.write(data)
    new_sha = hashlib.sha256(data).hexdigest()

    for doc in (inv, cand):
        for r in doc["records"]:
            if r["id"] == rid:
                old_sha = r["sha256"]
                r["sha256"] = new_sha

    print(f"{rid}: {len(data)}B sha {old_sha[:12]}→{new_sha[:12]}")

json.dump(inv, open(inv_path, "w"), indent=1)
json.dump(cand, open(cand_path, "w"), indent=1)

# Verify all three checksums now match
ok = all(
    hashlib.sha256(
        open(os.path.join(ROOT, records_by_id[rid]["fixture"]), "rb").read()
    ).hexdigest()
    == records_by_id[rid]["sha256"]
    for rid in ("sample-cer", "sample-crt", "sample-der")
)
print(f"checksum verification: {'PASS' if ok else 'FAIL'}")
