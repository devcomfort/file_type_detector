"""Probe numpy-stl binary save determinism."""

import sys
import io

sys.path.insert(0, ".")
import numpy as np  # noqa: E402
from stl import mesh  # noqa: E402

vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
faces = np.array([[0, 1, 2]])
m = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        m.vectors[i][j] = vertices[f[j]]

b1 = io.BytesIO()
m.save(b1)
b2 = io.BytesIO()
m.save(b2)
print("stl binary deterministic:", b1.getvalue() == b2.getvalue())
