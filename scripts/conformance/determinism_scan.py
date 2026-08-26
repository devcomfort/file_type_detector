"""Slow determinism scan: separate generate calls 2.1s apart to cross the
1-second localtime boundary that fast same-process double-runs miss."""

import json
import sys
import time

sys.path.insert(0, ".")

from scripts.generators import list_generators  # noqa: E402

out = {}
for name, cls in sorted(list_generators().items()):
    inst = cls()
    if getattr(inst, "category", "") == "download":
        continue
    for ext in inst.extensions:
        try:
            b1 = inst.generate(ext)
        except Exception as e:  # noqa: BLE001 - recorded
            out[ext] = {"error": repr(e)[:60]}
            continue
        time.sleep(2.1)
        try:
            b2 = inst.generate(ext)
        except Exception as e:  # noqa: BLE001
            out[ext] = {"error2": repr(e)[:60]}
            continue
        out[ext] = {"same": b1 == b2}

errors = {k: v for k, v in out.items() if "error" in v or "error2" in v}
tier2 = {"7z", "dxf", "stl"}
diffs = {k for k, v in out.items() if v.get("same") is False}
unexpected = diffs - tier2

if errors:
    print(f"FAIL: generator errors: {errors}", file=sys.stderr)
    sys.exit(1)
if unexpected:
    print(
        f"FAIL: nondeterministic generators outside Tier2: {sorted(unexpected)}",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"Determinism scan PASSED: {len(out)} checked, {len(diffs)} Tier2, 0 errors")
