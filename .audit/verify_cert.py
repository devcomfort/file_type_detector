"""Verify certificates.py is deterministic and produces valid certs."""

import sys
import hashlib

sys.path.insert(0, ".")
from scripts.generators.certificates import CertificateGenerator  # noqa: E402

g = CertificateGenerator()
b1 = g.generate("crt")
b2 = g.generate("crt")
d1 = g.generate("der")
d2 = g.generate("der")

print("pem deterministic:", b1 == b2)
print("der deterministic:", d1 == d2)
print("sha256 crt:", hashlib.sha256(b1).hexdigest())

from cryptography import x509  # noqa: E402

cert = x509.load_pem_x509_certificate(b1)
print("serial:", hex(cert.serial_number))
print(
    "validity:", cert.not_valid_before_utc.date(), "->", cert.not_valid_after_utc.date()
)
