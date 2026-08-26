"""Certificate format generators using cryptography library.

Certificate fixtures are byte-reproducible: the signing key is a committed
test-only key (``tests/truth/keys/test_signing_key.pem``), and serial number
and validity window are constants. The fixture reproducibility gate requires
identical bytes on every run.
"""

import datetime
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization

from .base import BaseGenerator
from . import register

_FIXED_KEY_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "truth"
    / "keys"
    / "test_signing_key.pem"
)
# Arbitrary but constant validity window (2026-01-01 .. 2027-01-01 UTC).
_FIXED_NOT_BEFORE = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
_FIXED_NOT_AFTER = datetime.datetime(2027, 1, 1, tzinfo=datetime.timezone.utc)
_FIXED_SERIAL = 0x5A5A5A5A5A5A5A5A


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
            "cer": "library:cryptography (fixed test key)",
            "crt": "library:cryptography (fixed test key)",
            "der": "library:cryptography (fixed test key)",
        }

    def generate(self, ext: str) -> bytes:
        generators = {
            "cer": self._create_der,
            "crt": self._create_pem,
            "der": self._create_der,
        }
        return generators[ext]()

    @staticmethod
    def _load_fixed_key():
        """Load the committed test signing key (deterministic across runs)."""
        return serialization.load_pem_private_key(
            _FIXED_KEY_PATH.read_bytes(), password=None
        )

    def _create_key_and_cert(self):
        key = self._load_fixed_key()
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "Sample"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(_FIXED_SERIAL)
            .not_valid_before(_FIXED_NOT_BEFORE)
            .not_valid_after(_FIXED_NOT_AFTER)
            .sign(key, hashes.SHA256())
        )
        return key, cert

    def _create_pem(self) -> bytes:
        _, cert = self._create_key_and_cert()
        return cert.public_bytes(serialization.Encoding.PEM)

    def _create_der(self) -> bytes:
        _, cert = self._create_key_and_cert()
        return cert.public_bytes(serialization.Encoding.DER)
