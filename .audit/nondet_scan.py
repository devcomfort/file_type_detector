"""Determinism scan over the real generator registry.

Aggregates every registered extension into exactly one of:
- deterministic: two in-process runs produce identical bytes
- nondeterministic: runs differ
- failed: generate() raised
- skipped_external: network-dependent download generator (not executed twice)

No silent excepts: failures are recorded with their error text.
"""

import json
import sys

sys.path.insert(0, ".")

from scripts.generators import list_generators  # noqa: E402

EXTERNAL_CATEGORY = "download"

result = {
    "deterministic": {},  # ext -> generator class name
    "nondeterministic": {},  # ext -> {class, lengths}
    "failed": {},  # ext -> {class, error}
    "skipped_external": {},  # ext -> class
}

for name, cls in sorted(list_generators().items()):
    try:
        instance = cls()
        exts = list(instance.extensions)
    except Exception as exc:  # noqa: BLE001 - recorded, never silent
        result["failed"]["<class:%s>" % name] = {"error": repr(exc)}
        continue

    if getattr(instance, "category", "") == EXTERNAL_CATEGORY:
        for ext in exts:
            result["skipped_external"][ext] = name
        continue

    for ext in exts:
        try:
            first = instance.generate(ext)
        except Exception as exc:  # noqa: BLE001
            result["failed"][ext] = {"class": name, "error": repr(exc)}
            continue
        try:
            second = instance.generate(ext)
        except Exception as exc:  # noqa: BLE001
            result["failed"][ext] = {"class": name, "error": f"second run: {exc!r}"}
            continue
        if first == second:
            result["deterministic"][ext] = name
        else:
            result["nondeterministic"][ext] = {
                "class": name,
                "run1_len": len(first),
                "run2_len": len(second),
            }

summary = {k: len(v) for k, v in result.items()}
print(json.dumps({"summary": summary, **result}, indent=1, sort_keys=True))
