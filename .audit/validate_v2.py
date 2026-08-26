"""Validate the v2 migration drafts with the real loader."""

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from scripts.conformance.inventory import (  # noqa: E402
    load_verified_inventory,
    review_summary,
)

candidates_path = Path("/tmp/candidates_v8.json")
inventory_path = Path("/tmp/inventory_v8.json")

records = load_verified_inventory(candidates_path, inventory_path, root=Path("."))
summary = review_summary(candidates_path, inventory_path, root=Path("."))
print(json.dumps({k: v for k, v in summary.items() if k != "unresolved"}, indent=1))
print("loaded records:", len(records))

by_id = {r.id: r for r in records}
for rid in ("sample-3dm", "sample-7z", "sample-png"):
    rec = by_id.get(rid)
    if rec and rec.source_integrity:
        print(
            f"{rid}: kind={rec.source_integrity.kind} tier={rec.source_integrity.tier}"
        )
