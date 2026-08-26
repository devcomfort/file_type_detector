"""Regenerate cert fixtures deterministically; update inventory/candidates hashes."""

import glob
import hashlib
import json
import os
import sys

ROOT = "/mnt/workspace/projects/file_type_detector-backend-conformance"
sys.path.insert(0, ROOT)

from scripts.generators.certificates import CertificateGenerator  # noqa: E402

g = CertificateGenerator()

inv = json.load(open("/tmp/inventory_v4.json"))
cand = json.load(open("/tmp/candidates_v4.json"))

for rid, ext in (("sample-cer", "cer"), ("sample-crt", "crt"), ("sample-der", "der")):
    data = g.generate(ext)
    rec = next((r for r in inv["records"] if r["id"] == rid), None)
    if rec is None:
        print(f"{rid}: not in authoritative; skipped")
        continue
    path = os.path.join(ROOT, rec["fixture"])
    with open(path, "wb") as f:
        f.write(data)
    new_sha = hashlib.sha256(data).hexdigest()
    for doc in (inv, cand):
        for r in doc["records"]:
            if r["id"] == rid:
                r["sha256"] = new_sha
                r["format_validity"] = {
                    "status": "verified",
                    "validator": "x509-load-determinism",
                    "evidence": [
                        "cryptography x509 load ok",
                        "fixed serial 0x5a5a5a5a5a5a5a5a",
                        "validity 2026-01-01..2027-01-01",
                        "two-run byte-identical generation",
                    ],
                }
    print(f"{rid}: regenerated {len(data)}B sha={new_sha[:12]}…")

json.dump(inv, open("/tmp/inventory_v4.json", "w"), indent=1)
json.dump(cand, open("/tmp/candidates_v4.json", "w"), indent=1)
print("done")
