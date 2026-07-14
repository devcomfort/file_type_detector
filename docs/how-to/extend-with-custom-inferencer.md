# Extend with a Custom Inferencer

This guide shows how to add a new inferencer to the library.

## 1. Subclass `BaseInferencer`

Every inferencer implements the same `infer` method.

```python
from pathlib import Path
from typing import Union

from filetype_detector import BaseInferencer, FileType


class MyInferencer(BaseInferencer):
    def infer(self, file_path: Union[Path, str]) -> FileType:
        path_obj = Path(file_path)

        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path_obj}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path_obj}")

        return FileType.from_extension(".custom")
```

## 2. Use It Directly

You do not need to register a backend if direct construction is enough.

```python
inferencer = MyInferencer()
ft = inferencer.infer("sample.dat")
'.custom' in ft.extensions  # True
```

## 3. Register It in `AutoInferencer`

If you want the new inferencer available through `AutoInferencer`, update the backend type and backend map in `src/filetype_detector/auto_inferencer.py`.

```python
BackendType = Literal["lexical", "magic", "magika", "hybrid", "custom"]

_BACKEND_MAP = {
    "lexical": LexicalInferencer,
    "magic": MagicInferencer,
    "magika": MagikaInferencer,
    "hybrid": HybridInferencer,
    "custom": MyInferencer,
}
```

## 4. Add Tests

Create a dedicated test module that checks:

- normal inference
- missing-file behavior
- directory-path behavior
- backend registration, if you expose it through `AutoInferencer`

## 5. Update Documentation

Add or update:

- the relevant API reference page
- how-to examples if the new inferencer solves a common task
- architecture notes if the new strategy changes the design story

See [Contributing](../contributing.md) for the full project workflow.