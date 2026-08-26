"""Measure magika parity by model output: run every fixture through magika
and record result.output.label, then compare against the model label space."""

import json
import sys

sys.path.insert(0, ".")

from magika import Magika  # noqa: E402

m = Magika()
labels = set(m._model_config.target_labels_space)

inv = json.load(open("tests/truth/backend_inventory.json"))
recs = inv["records"]

label_hits: dict[str, list[str]] = {}
unresolved: list[str] = []
for r in recs:
    try:
        result = m.identify_path(r["fixture"])
        lab = result.output.label
    except Exception as e:  # noqa: BLE001 - recorded, never silent
        unresolved.append(f"{r['id']}: {e!r}")
        continue
    if lab in labels:
        label_hits.setdefault(lab, []).append(r["id"])
    else:
        unresolved.append(f"{r['id']}: non-target label {lab!r}")

internal_excluded = {"randombytes", "randomtxt"}
real_labels = {l for l in labels if l not in internal_excluded}

covered = sorted(set(label_hits) & real_labels)
missing = sorted(real_labels - set(label_hits))

print(
    json.dumps(
        {
            "model_labels_total": len(labels),
            "real_labels": len(real_labels),
            "covered_by_model_output": len(covered),
            "missing_from_model_output": len(missing),
            "missing_list": missing,
            "fixtures_unresolvable": unresolved[:10],
        },
        indent=1,
    )
)
