"""Reproduce the JXL KeyError without explicit plugin import."""

import sys

sys.path.insert(0, ".")

from PIL import Image  # noqa: E402

img = Image.new("RGB", (8, 8), (255, 0, 0))
buf = "/tmp/probe.jxl"
try:
    img.save(buf, format="JXL")
    print("JXL saved WITHOUT explicit pillow_jxl import")
except Exception as e:
    print("fails without import:", type(e).__name__, str(e)[:100])
