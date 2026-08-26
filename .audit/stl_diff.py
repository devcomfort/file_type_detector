"""Locate differing bytes between two numpy-stl saves (temp file mode)."""

import os
import tempfile

import numpy as np
from stl import mesh

vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
faces = np.array([[0, 1, 2]])
m = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        m.vectors[i][j] = vertices[f[j]]


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
print("lengths:", len(a), len(b))
print("first diffs:", diffs[:8])
