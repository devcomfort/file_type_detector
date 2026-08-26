"""Promote cer/crt/der to authoritative with regenerated deterministic fixtures."""

import copy
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
    new_sha = hashlib.sha256(data).hexdigest()
    rec = next(r for r in cand["records"] if r["id"] == rid)
    path = os.path.join(ROOT, rec["fixture"])
    with open(path, "wb") as f:
        f.write(data)
    rec["sha256"] = new_sha
    rec["format_validity"] = {
        "status": "verified",
        "validator": "x509-load-determinism",
        "evidence": [
            "cryptography x509 load ok",
            "fixed serial 0x5a5a5a5a5a5a5a5a",
            "validity 2026-01-01..2027-01-01",
            "two-run byte-identical generation",
        ],
    }
    rec["ground_truth_review"] = {
        "status": "verified",
        "reviewed_by": "fixture-curation-batch",
        "reviewed_at": "2026-08-24",
        "evidence": [".audit/verify_cert.py: deterministic + x509 load + fixed fields"],
    }
    inv["records"].append(copy.deepcopy(rec))
    print(f"{rid}: promoted, {len(data)}B sha={new_sha[:12]}…")

json.dump(inv, open("/tmp/inventory_v4.json", "w"), indent=1)
json.dump(cand, open("/tmp/candidates_v4.json", "w"), indent=1)
print("inventory:", len(inv["records"]))
