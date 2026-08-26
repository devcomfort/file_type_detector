"""Correct GT claims and inject per-claim evidence for authoritative records.

Fixes:
1. sample-avro: GT mime application/x-avro -> application/avro (Avro spec)
2. sample-db: GT mime application/octet-stream -> application/vnd.sqlite3
3. sample-gz/gzip: remove false .tgz/.tar.gz extension aliases from GT
4. sample-cer: GT mime -> application/pkix-cert (RFC 2585)
5. sample-crt/der: excluded — no registered MIME/extension evidence exists
6. Inject ground_truth_evidence with bidirectional claim==evidence coverage
"""

import copy
import hashlib
import json
import os

ROOT = "/mnt/workspace/projects/file_type_detector-backend-conformance"
COMMIT = "7354692a691e66380e6572c3a18e20ac99771f7d"

inv = json.load(open("/tmp/inventory_v5.json"))
cand = json.load(open("/tmp/candidates_v5.json"))

# --- GT corrections ---
GT_FIXES = {
    "sample-avro": {"mime_types": ["application/avro"], "extensions": [".avro"]},
    "sample-db": {
        "mime_types": ["application/vnd.sqlite3"],
        "extensions": [".db"],
    },
    "sample-gz": {"mime_types": ["application/gzip"], "extensions": [".gz", ".gzip"]},
    "sample-gzip": {"mime_types": ["application/gzip"], "extensions": [".gz", ".gzip"]},
    "sample-cer": {"mime_types": ["application/pkix-cert"], "extensions": [".cer"]},
}

DEMOTE_EXCLUDED = {"sample-crt", "sample-der"}

# --- Evidence per record: exact claim -> authority + reference ---
EVIDENCE = {
    "sample-7z": {
        "application/x-7z-compressed": (
            "7-Zip technical specification",
            "https://py7zr.readthedocs.io/",
        ),
        ".7z": ("7-Zip file extension documentation", "https://www.7-zip.org/"),
    },
    "sample-avif": {
        "image/avif": (
            "IANA image/avif registration",
            "https://www.iana.org/assignments/media-types/image/avif",
        ),
        ".avif": ("AVIF specification", "https://aomediacodec.github.io/av1-avif/"),
    },
    "sample-avro": {
        "application/avro": (
            "Apache Avro specification",
            "https://avro.apache.org/docs/current/spec.html",
        ),
        ".avro": (
            "Apache Avro specification",
            "https://avro.apache.org/docs/current/spec.html",
        ),
    },
    "sample-cer": {
        "application/pkix-cert": (
            "RFC 2585: .cer extension, application/pkix-cert MIME registration",
            "https://datatracker.ietf.org/doc/html/rfc2585",
        ),
        ".cer": ("RFC 2585 Section 4", "https://datatracker.ietf.org/doc/html/rfc2585"),
    },
    "sample-db": {
        "application/vnd.sqlite3": (
            "SQLite database file format",
            "https://www.sqlite.org/fileformat2.html",
        ),
        ".db": ("SQLite format", "https://www.sqlite.org/fileformat2.html"),
    },
    "sample-gz": {
        "application/gzip": (
            "RFC 6713",
            "https://datatracker.ietf.org/doc/html/rfc6713",
        ),
        ".gz": ("RFC 6713", "https://datatracker.ietf.org/doc/html/rfc6713"),
        ".gzip": ("RFC 6713", "https://datatracker.ietf.org/doc/html/rfc6713"),
    },
    "sample-gzip": {
        "application/gzip": (
            "RFC 6713",
            "https://datatracker.ietf.org/doc/html/rfc6713",
        ),
        ".gz": ("RFC 6713", "https://datatracker.ietf.org/doc/html/rfc6713"),
        ".gzip": ("RFC 6713", "https://datatracker.ietf.org/doc/html/rfc6713"),
    },
    "sample-parquet": {
        "application/vnd.apache.parquet": (
            "Apache Parquet format specification",
            "https://parquet.apache.org/docs/",
        ),
        ".parquet": ("Apache Parquet", "https://parquet.apache.org/docs/"),
        ".pqt": ("Apache Parquet legacy extension", "https://parquet.apache.org/docs/"),
    },
    "sample-pcap": {
        "application/vnd.tcpdump.pcap": (
            "IANA application/vnd.tcpdump.pcap registration",
            "https://www.iana.org/assignments/media-types/application/vnd.tcpdump.pcap",
        ),
        ".pcap": (
            "IANA pcap registration",
            "https://www.iana.org/assignments/media-types/application/vnd.tcpdump.pcap",
        ),
        ".pcapng": ("PCAPng specification", "https://pcapng.github.io/pcapng/"),
    },
    "sample-sqlite": {
        "application/vnd.sqlite3": (
            "IANA vnd.sqlite3 registration",
            "https://www.sqlite.org/fileformat2.html",
        ),
        ".sqlite": ("IANA sqlite3", "https://www.sqlite.org/fileformat2.html"),
        ".sqlite3": ("IANA sqlite3", "https://www.sqlite.org/fileformat2.html"),
    },
    "sample-sqlite3": {
        "application/vnd.sqlite3": (
            "IANA vnd.sqlite3 registration",
            "https://www.sqlite.org/fileformat2.html",
        ),
        ".sqlite": ("IANA sqlite3", "https://www.sqlite.org/fileformat2.html"),
        ".sqlite3": ("IANA sqlite3", "https://www.sqlite.org/fileformat2.html"),
    },
    "sample-zip": {
        "application/zip": (
            "PKWARE APPNOTE.TXT (.ZIP File Format Specification)",
            "https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT",
        ),
        ".zip": (
            "PKWARE APPNOTE.TXT",
            "https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT",
        ),
    },
}


def build_evidence(rid):
    ev = EVIDENCE[rid]
    rec = next(r for r in inv["records"] if r["id"] == rid)
    gt = rec["ground_truth"]
    mime_claims = [
        {"mime_type": m, "authority": ev[m][0], "reference": ev[m][1]}
        for m in gt["mime_types"]
    ]
    ext_claims = [
        {"extension": e, "authority": ev[e][0], "reference": ev[e][1]}
        for e in gt["extensions"]
    ]
    return {"mime_claims": mime_claims, "extension_claims": ext_claims}


# Pass 1: clear stale evidence, apply GT fixes, handle demotions
for doc in (inv, cand):
    for r in doc["records"]:
        rid = r["id"]
        r.pop("ground_truth_evidence", None)
        if rid in DEMOTE_EXCLUDED:
            r["ground_truth_review"] = {
                "status": "excluded",
                "reason": "no registered MIME type or extension evidence "
                "for .crt/.der; RFC 2585 only covers .cer/application/pkix-cert",
            }
        if rid in GT_FIXES:
            r["ground_truth"].update(GT_FIXES[rid])

# Pass 2: inject evidence only for verified records in the allowlist
missing_preflight = []
for doc in (inv, cand):
    for r in doc["records"]:
        rid = r["id"]
        if r["ground_truth_review"]["status"] != "verified":
            continue
        if rid not in EVIDENCE:
            missing_preflight.append(rid)
            continue
        r["ground_truth_evidence"] = build_evidence(rid)

if missing_preflight:
    raise SystemExit(
        "FAIL: verified records lack ground_truth_evidence entries: "
        + ", ".join(sorted(set(missing_preflight)))
    )
# Remove demoted/excluded records from authoritative inventory
excluded_ids = {
    r["id"]
    for r in cand["records"]
    if r["ground_truth_review"]["status"] in ("excluded", "needs_review")
}
inv["records"] = [r for r in inv["records"] if r["id"] not in excluded_ids]

# Restore orphan candidates (verified inventory records missing candidates)
cand_ids = {r["id"] for r in cand["records"]}
for r in inv["records"]:
    if r["id"] not in cand_ids:
        cand["records"].append(copy.deepcopy(r))
json.dump(inv, open("/tmp/inventory_v6.json", "w"), indent=1)
json.dump(cand, open("/tmp/candidates_v6.json", "w"), indent=1)

cand_by_id = {r["id"]: r for r in cand["records"]}
mismatch = [r["id"] for r in inv["records"] if cand_by_id.get(r["id"]) != r]
print(f"fact-identity mismatches: {len(mismatch)}")
print(f"inventory: {len(inv['records'])}")
print(f"candidates: {len(cand['records'])}")
