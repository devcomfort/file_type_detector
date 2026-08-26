"""Collect certificate validation evidence: determinism + x509 load + fixture match."""

import hashlib
import json
import os
import sys

sys.path.insert(0, ".")

from scripts.generators.certificates import CertificateGenerator  # noqa: E402
from cryptography import x509  # noqa: E402

g = CertificateGenerator()
results = {}
for ext in ("cer", "crt", "der"):
    b1 = g.generate(ext)
    cert = (
        x509.load_pem_x509_certificate(b1)
        if ext == "crt"
        else x509.load_der_x509_certificate(b1)
    )
    results[ext] = {
        "deterministic": b1 == g.generate(ext),
        "serial": hex(cert.serial_number),
        "validity": [
            str(cert.not_valid_before_utc.date()),
            str(cert.not_valid_after_utc.date()),
        ],
        "sha256": hashlib.sha256(b1).hexdigest(),
    }

inv = json.load(open("tests/truth/backend_inventory.json"))
for r in inv["records"]:
    if r["id"] in ("sample-cer", "sample-crt", "sample-der"):
        disk = open(r["fixture"], "rb").read()
        gen = g.generate(r["probe_extension"].lstrip("."))
        results[r["id"]] = {
            "committed_matches_generator": disk == gen,
            "committed_sha_matches_inventory": hashlib.sha256(disk).hexdigest()
            == r["sha256"],
        }

print(json.dumps(results, indent=1))
