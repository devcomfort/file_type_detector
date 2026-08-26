"""Check library APIs for metadata control (py7zr, fastavro, scapy)."""

import sys
import inspect

sys.path.insert(0, ".")
import py7zr  # noqa: E402
import fastavro  # noqa: E402
from scapy.all import PcapWriter  # noqa: E402

print("SevenZipFile init:", inspect.signature(py7zr.SevenZipFile.__init__))
print("writestr:", inspect.signature(py7zr.SevenZipFile.writestr))
print("writer:", inspect.signature(fastavro.writer))
print("PcapWriter:", inspect.signature(PcapWriter.__init__))
