"""Detail why magika mislabels fixtures that exist for missing labels."""

import json
import os
import sys

sys.path.insert(0, ".")

from magika import Magika  # noqa: E402

m = Magika()
inv = json.load(open("tests/truth/backend_inventory.json"))
recs = {r["id"]: r for r in inv["records"]}
missing = json.load(open("/tmp/parity.json"))["missing_list"]

out = []
for lab in missing:
    rid = f"sample-{lab}"
    rec = recs.get(rid)
    if not rec:
        continue
    res = m.identify_path(rec["fixture"])
    out.append(
        {
            "label": lab,
            "id": rid,
            "magika_says": res.output.label,
            "size": os.path.getsize(rec["fixture"]),
        }
    )

print(json.dumps(out, indent=1))
