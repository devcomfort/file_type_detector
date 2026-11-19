# UnifiedInferencer

Unified interface for selecting an inferencer backend with a single class.

```python
from filetype_detector import UnifiedInferencer, BackendType
```

## Overview

`UnifiedInferencer` wraps the available inferencer implementations behind one constructor.
Instead of importing a different class for each strategy, you choose a backend with the
`backend` argument.

Available backends:

- `"lexical"`: Uses `LexicalInferencer`
- `"magic"`: Uses `MagicInferencer`
- `"magika"`: Uses `MagikaInferencer`
- `"hybrid"`: Uses `HybridInferencer`
- `"tika"`: Uses `TikaInferencer` (Apache Tika; OS-independent labels; requires Java and the pinned JAR)

## Type Definition

```python
BackendType = Literal["lexical", "magic", "magika", "hybrid", "tika"]
```

## Basic Usage

Content-based backends require the supplied path to reference an existing regular file.

```python
from filetype_detector import UnifiedInferencer

inferencer = UnifiedInferencer(backend="magic")
ft = inferencer.detect("file_without_ext")
ft.extensions   # e.g. ('.pdf',) based on content
ft.mime_types   # e.g. ('application/pdf',)
```

`detect()` always returns a `FileType` instance regardless of the backend.

## Backend Selection

### `backend="lexical"`

Fastest option. Extracts the extension from the path without reading file content.

```python
inferencer = UnifiedInferencer(backend="lexical")
ft = inferencer.detect("document.pdf")
'.pdf' in ft.extensions  # True
```

### `backend="magic"`

Uses libmagic through `python-magic` to infer the type from file content.

```python
inferencer = UnifiedInferencer(backend="magic")
ft = inferencer.detect("file.dat")
ft.extensions  # e.g. ('.pdf',) based on content
```

### `backend="magika"`

Uses Google's Magika model for content-based detection.

```python
inferencer = UnifiedInferencer(backend="magika")
ft = inferencer.detect("script.py")
'.py' in ft.extensions  # True
```

`UnifiedInferencer` returns a `FileType`. If you also need confidence scores,
use `MagikaInferencer` directly via `detect_with_score()`.

### `backend="hybrid"`

Uses `HybridInferencer`, which runs Magic first and applies Magika to generic or ambiguous results.

```python
inferencer = UnifiedInferencer(backend="hybrid")
ft = inferencer.detect("document.pdf")
'.pdf' in ft.extensions  # True
```

This is the recommended default when you want a good balance between performance and accuracy.

### `backend="tika"`

Uses `TikaInferencer`, which runs a pinned Apache Tika build (3.3.3) in a long-lived JVM process.
A pinned build returns identical MIME and extension labels on Linux, macOS, and Windows, so
results do not depend on the host OS MIME database.

Requires Java 11+ on `PATH` and the pinned `tika-app-3.3.3.jar`. Resolve the JAR with an explicit
`jar_path`, the `TIKA_JAR` environment variable, or the default cache path
(`~/.cache/filetype-detector/tika-app-3.3.3.jar`). Verify or fetch it once:

```python
from filetype_detector import TikaInferencer

TikaInferencer.download_jar()  # one-time; SHA-512 verified
inferencer = UnifiedInferencer(backend="tika")
ft = inferencer.detect("document.pdf")
'.pdf' in ft.extensions  # True
```


## Example: Configuration-Based Selection

```python
from filetype_detector import UnifiedInferencer, BackendType, FileType

def detect(file_path: str, backend: BackendType = "hybrid") -> FileType:
    inferencer = UnifiedInferencer(backend=backend)
    return inferencer.detect(file_path)
```

## Example: Routing by File Type

```python
from pathlib import Path
from typing import Callable

from filetype_detector import UnifiedInferencer, BackendType


class FileRouter:
    def __init__(self, backend: BackendType = "magic"):
        self.inferencer = UnifiedInferencer(backend=backend)
        self.handlers: dict[str, Callable] = {}

    def register(self, extension: str, handler: Callable) -> None:
        self.handlers[extension] = handler

    def route(self, file_path: Path):
        ft = self.inferencer.detect(file_path)
        # Check each detected extension against registered handlers
        for ext in ft.extensions:
            handler = self.handlers.get(ext)
            if handler:
                return handler(file_path)
        return None
```

## Exceptions

`UnifiedInferencer.detect()` forwards the behavior of the selected backend.

- `backend="lexical"`: Raises `ValueError` when the path has no extension
- `backend="magic"`, `"magika"`, `"hybrid"`, `"tika"`: May raise `FileNotFoundError`, `ValueError`, or `RuntimeError`
- `backend="tika"`: Additionally requires Java 11+ and the verified pinned JAR before first `detect()`

## When to Use Direct Inferencer Classes

Use `UnifiedInferencer` when you want one entry point and type-safe backend selection.
Use the concrete inferencer classes directly when you need backend-specific behavior,
such as `MagikaInferencer.detect_with_score()`.
