"""Inject ground_truth_evidence into the 14 authoritative records (schema v2)."""

import json

inv = json.load(open("/tmp/inventory_v5.json"))
cand = json.load(open("/tmp/candidates_v5.json"))

EVIDENCE_MIME = json.load(open("/tmp/evidence_mime.json"))
CERT_EXT = json.load(open("/tmp/evidence_ext_cert.json"))

for doc in (inv, cand):
    for r in doc["records"]:
        if r["ground_truth_review"]["status"] != "verified":
            continue
        rid = r["id"]
        gt = r["ground_truth"]
        mime_claims = []
        for m in gt["mime_types"]:
            ev = EVIDENCE_MIME.get(rid)
            if ev is None:
                authority = "IANA pkix registration"
                reference = "https://datatracker.ietf.org/doc/html/rfc2585"
            else:
                authority = ev["authority"]
                reference = ev["reference"]
            mime_claims.append(
                {"mime_type": m, "authority": authority, "reference": reference}
            )
        ext_claims = []
        for e in gt["extensions"]:
            ev = CERT_EXT.get(e)
            if ev:
                ext_claims.append({"extension": e, **ev})
            else:
                ref = mime_claims[0]["reference"] if mime_claims else ""
                ext_claims.append(
                    {
                        "extension": e,
                        "authority": "inherited from MIME registration",
                        "reference": ref,
                    }
                )
        r["ground_truth_evidence"] = {
            "mime_claims": mime_claims,
            "extension_claims": ext_claims,
        }

json.dump(inv, open("/tmp/inventory_v5.json", "w"), indent=1)
json.dump(cand, open("/tmp/candidates_v5.json", "w"), indent=1)
print("evidence injected")
