# AutoInferencer

Unified interface for selecting an inferencer backend with a single class.

```python
from filetype_detector import AutoInferencer, BackendType
```

## Overview

`AutoInferencer` wraps the available inferencer implementations behind one constructor.
Instead of importing a different class for each strategy, you choose a backend with the
`backend` argument.

Available backends:

- `"lexical"`: Uses `LexicalInferencer`
- `"magic"`: Uses `MagicInferencer`
- `"magika"`: Uses `MagikaInferencer`
- `"hybrid"`: Uses `HybridInferencer`

## Type Definition

```python
BackendType = Literal["lexical", "magic", "magika", "hybrid"]
```

## Basic Usage

Content-based backends require the supplied path to reference an existing regular file.

```python
from filetype_detector import AutoInferencer

inferencer = AutoInferencer(backend="magic")
ft = inferencer.infer("file_without_ext")
ft.extensions   # e.g. ('.pdf',) based on content
ft.mime_types   # e.g. ('application/pdf',)
```

`infer()` always returns a `FileType` instance regardless of the backend.

## Backend Selection

### `backend="lexical"`

Fastest option. Extracts the extension from the path without reading file content.

```python
inferencer = AutoInferencer(backend="lexical")
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions  # True
```

### `backend="magic"`

Uses libmagic through `python-magic` to infer the type from file content.

```python
inferencer = AutoInferencer(backend="magic")
ft = inferencer.infer("file.dat")
ft.extensions  # e.g. ('.pdf',) based on content
```

### `backend="magika"`

Uses Google's Magika model for content-based detection.

```python
inferencer = AutoInferencer(backend="magika")
ft = inferencer.infer("script.py")
'.py' in ft.extensions  # True
```

`AutoInferencer` returns a `FileType`. If you also need confidence scores,
use `MagikaInferencer` directly via `infer_with_score()`.

### `backend="hybrid"`

Uses `HybridInferencer`, which runs Magic first and applies Magika to generic or ambiguous results.

```python
inferencer = AutoInferencer(backend="hybrid")
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions  # True
```

This is the recommended default when you want a good balance between performance and accuracy.

## Example: Configuration-Based Selection

```python
from filetype_detector import AutoInferencer, BackendType, FileType

def detect(file_path: str, backend: BackendType = "hybrid") -> FileType:
    inferencer = AutoInferencer(backend=backend)
    return inferencer.infer(file_path)
```

## Example: Routing by File Type

```python
from pathlib import Path
from typing import Callable

from filetype_detector import AutoInferencer, BackendType


class FileRouter:
    def __init__(self, backend: BackendType = "magic"):
        self.inferencer = AutoInferencer(backend=backend)
        self.handlers: dict[str, Callable] = {}

    def register(self, extension: str, handler: Callable) -> None:
        self.handlers[extension] = handler

    def route(self, file_path: Path):
        ft = self.inferencer.infer(file_path)
        # Check each detected extension against registered handlers
        for ext in ft.extensions:
            handler = self.handlers.get(ext)
            if handler:
                return handler(file_path)
        return None
```

## Exceptions

`AutoInferencer.infer()` forwards the behavior of the selected backend.

- `backend="lexical"`: Raises `ValueError` when the path has no extension
- `backend="magic"`, `"magika"`, `"hybrid"`: May raise `FileNotFoundError`, `ValueError`, or `RuntimeError`

## When to Use Direct Inferencer Classes

Use `AutoInferencer` when you want one entry point and type-safe backend selection.
Use the concrete inferencer classes directly when you need backend-specific behavior,
such as `MagikaInferencer.infer_with_score()`.
