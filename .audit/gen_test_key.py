"""One-time bootstrap: generate the fixed RSA test key used by certificates.py.

Run once; commit the emitted PEM as tests/truth/test_key.pem. The generator
reloads this key at build time, making certificate fixtures byte-reproducible.
"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
pem = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
)
print(pem.decode())

k2 = serialization.load_pem_private_key(pem, password=None)
print(
    "reload-ok:", k2.public_key().public_numbers() == key.public_key().public_numbers()
)
