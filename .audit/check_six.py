"""Check if committed fixtures match current deterministic generator output."""

import hashlib
import json
import sys

sys.path.insert(0, ".")
from scripts.generators.certificates import CertificateGenerator  # noqa: E402

g = CertificateGenerator()
results = {}

for ext in ("cer", "crt", "der"):
    gen = g.generate(ext)
    results[f"sample-{ext}"] = {
        "gen_sha256": hashlib.sha256(gen).hexdigest(),
        "gen_len": len(gen),
    }

inv = json.load(open("tests/truth/backend_inventory.json"))
for r in inv["records"]:
    rid = r["id"]
    if rid in ("sample-cer", "sample-crt", "sample-der"):
        disk = open(r["fixture"], "rb").read()
        gen = g.generate(r["probe_extension"].lstrip("."))
        results[rid]["disk_sha256"] = r["sha256"]
        results[rid]["match"] = disk == gen
        results[rid]["needs_regen"] = not (disk == gen)

print(json.dumps(results, indent=1))
