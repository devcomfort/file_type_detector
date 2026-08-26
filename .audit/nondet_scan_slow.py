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

print(json.dumps(out))
