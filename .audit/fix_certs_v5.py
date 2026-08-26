"""Re-promote cer/crt/der in v5 (they were demoted by the bulk conversion)."""

import json
import sys

ROOT = "/mnt/workspace/projects/file_type_detector-backend-conformance"
sys.path.insert(0, ROOT)

cand = json.load(open("/tmp/candidates_v5.json"))
inv = json.load(open("/tmp/inventory_v5.json"))

CERT_EVIDENCE = {
    "validator": "x509-load-determinism",
    "evidence": [
        "cryptography x509 load ok",
        "fixed serial 0x5a5a5a5a5a5a5a5a",
        "validity 2026-01-01..2027-01-01",
        "two-run byte-identical generation",
    ],
}

for rid in ("sample-cer", "sample-crt", "sample-der"):
    rec = next(x for x in cand["records"] if x["id"] == rid)
    rec["format_validity"] = {"status": "verified", **CERT_EVIDENCE}
    rec["ground_truth_review"] = {
        "status": "verified",
        "reviewed_by": "fixture-curation-batch",
        "reviewed_at": "2026-08-24",
        "evidence": [".audit/verify_cert.py: deterministic + x509 load + fixed fields"],
    }
    if not any(x["id"] == rid for x in inv["records"]):
        inv["records"].append(rec)

json.dump(cand, open("/tmp/candidates_v5.json", "w"), indent=1)
json.dump(inv, open("/tmp/inventory_v5.json", "w"), indent=1)

from collections import Counter  # noqa: E402

statuses = Counter(r["ground_truth_review"]["status"] for r in cand["records"])
print("candidate statuses:", dict(statuses))
print("inventory:", len(inv["records"]))
