"""Re-verify avro/pcap determinism under the CI lock environment."""

import sys
import io
import json
import importlib.metadata as im

sys.path.insert(0, ".")
from scripts.generators.data_formats import DataFormatGenerator  # noqa: E402

g = DataFormatGenerator()
a1 = g.generate("avro")
a2 = g.generate("avro")
p1 = g.generate("pcap")
p2 = g.generate("pcap")
print(
    json.dumps(
        {
            "versions": {p: im.version(p) for p in ("fastavro", "scapy")},
            "avro_deterministic": a1 == a2,
            "pcap_deterministic": p1 == p2,
        }
    )
)
