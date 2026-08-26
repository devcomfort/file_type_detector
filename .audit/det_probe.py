"""Probe determinism: fastavro fixed sync_marker, scapy fixed packet time."""

import sys
import io
import json

sys.path.insert(0, ".")

results = {}

import fastavro  # noqa: E402

schema = {"type": "record", "name": "R", "fields": [{"name": "a", "type": "string"}]}
buf1 = io.BytesIO()
fastavro.writer(buf1, schema, [{"a": "x"}], sync_marker=b"\x00" * 16)
buf2 = io.BytesIO()
fastavro.writer(buf2, schema, [{"a": "x"}], sync_marker=b"\x00" * 16)
results["fastavro_fixed_sync"] = buf1.getvalue() == buf2.getvalue()

from scapy.all import IP, UDP, Raw, PcapWriter  # noqa: E402


def make_pcap():
    b = io.BytesIO()
    pkt = IP(src="1.2.3.4", dst="5.6.7.8") / UDP(dport=53) / Raw(b"test")
    pkt.time = 1700000000
    w = PcapWriter(b, linktype=1, nano=False, sync=True)
    w.write(pkt)
    w.flush()
    data = b.getvalue()
    return data


p1, p2 = make_pcap(), make_pcap()
results["scapy_pcap_fixed_time"] = p1 == p2

print(json.dumps(results, indent=1))
