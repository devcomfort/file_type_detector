"""Test whether pinning mesh.name makes numpy-stl save deterministic."""

import os
import sys
import tempfile

sys.path.insert(0, ".")
import numpy as np  # noqa: E402
from stl import mesh  # noqa: E402

m_probe = mesh.Mesh(np.zeros(1, dtype=mesh.Mesh.dtype))
print("has name attr:", hasattr(m_probe, "name"), getattr(m_probe, "name", None))

vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
faces = np.array([[0, 1, 2]])
m = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        m.vectors[i][j] = vertices[f[j]]
m.name = "fixedname"


def make():
    fd, tmp = tempfile.mkstemp(suffix=".stl")
    os.close(fd)
    try:
        m.save(tmp)
        with open(tmp, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp)


a, b = make(), make()
diffs = [(i, a[i], b[i]) for i in range(min(len(a), len(b))) if a[i] != b[i]]
print("with fixed name -> deterministic:", a == b, "| diffs:", diffs[:4])
