"""Check Pillow JXL support status."""

from PIL import Image, features
import PIL

print("Pillow:", PIL.__version__)
try:
    import pillow_jxl  # noqa: F401

    print("pillow_jxl available")
except ImportError as e:
    print("pillow_jxl NOT installed:", e)
img = Image.new("RGB", (8, 8), (255, 0, 0))
try:
    img.save("/tmp/t.jxl", format="JXL")
    print("save JXL ok")
except Exception as e:
    print("save JXL fails:", type(e).__name__, e)
