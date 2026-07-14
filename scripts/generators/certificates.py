"""Certificate format generators using cryptography library."""

import datetime

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .base import BaseGenerator
from . import register


@register
class CertificateGenerator(BaseGenerator):
    """Generates minimal valid certificate files."""

    @property
    def extensions(self) -> list[str]:
        return ["cer", "crt", "der"]

    @property
    def category(self) -> str:
        return "certificate"

    @property
    def sources(self) -> dict[str, str]:
        return {
            "cer": "library:cryptography",
            "crt": "library:cryptography",
            "der": "library:cryptography",
        }

    def generate(self, ext: str) -> bytes:
        generators = {
            "cer": self._create_der,
            "crt": self._create_pem,
            "der": self._create_der,
        }
        return generators[ext]()

    def _create_key_and_cert(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "Sample"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        return key, cert

    def _create_pem(self) -> bytes:
        _, cert = self._create_key_and_cert()
        return cert.public_bytes(serialization.Encoding.PEM)

    def _create_der(self) -> bytes:
        _, cert = self._create_key_and_cert()
        return cert.public_bytes(serialization.Encoding.DER)
