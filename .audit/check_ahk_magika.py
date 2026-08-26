"""Verify magika recognizes sample.ahk and check its label."""

import json
import os
import sys

ROOT = "/mnt/workspace/projects/file_type_detector-backend-conformance"
sys.path.insert(0, ROOT)

from magika import Magika  # noqa: E402

m = Magika()
data = open(os.path.join(ROOT, "tests/fixtures/sample.ahk"), "rb").read()
result = m.identify_bytes(data)

labels = sorted(m._model_config.target_labels_space)
print(f"magika label: {result.output.label}")
print(f"magika mime: {result.output.mime_type}")
print(f"magika ext: {result.output.extensions}")
print(f"'autohotkey' in labels: {'autohotkey' in labels}")
print(f"total labels: {len(labels)}")
