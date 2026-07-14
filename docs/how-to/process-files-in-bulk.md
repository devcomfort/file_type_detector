# Process Files in Bulk

This guide shows how to run file type detection efficiently across many files.

## Reuse One Inferencer Instance

Create the inferencer once and reuse it.
This is especially important for `MagikaInferencer` and `HybridInferencer`, because repeated construction adds avoidable overhead.

```python
from pathlib import Path

from filetype_detector import AutoInferencer, FileType

inferencer = AutoInferencer(backend="hybrid")

for file_path in Path("./documents").rglob("*"):
    if file_path.is_file():
        ft = inferencer.infer(file_path)
        print(file_path, ft.extensions)
```

## Handle Errors Per File

Batch jobs should usually continue when one file fails.

```python
from pathlib import Path

from filetype_detector import AutoInferencer, FileType


def detect_many(file_paths: list[Path]) -> dict[str, FileType]:
    inferencer = AutoInferencer(backend="hybrid")
    results: dict[str, FileType] = {}

    for file_path in file_paths:
        try:
            results[str(file_path)] = inferencer.infer(file_path)
        except Exception as exc:
            results[str(file_path)] = FileType(extensions=(f"ERROR: {exc}",), mime_types=())

    return results
```

## Scan Directories

Use `Path.rglob()` when you want recursive detection.

```python
from collections import Counter
from pathlib import Path

from filetype_detector import AutoInferencer


def scan_directory(directory: Path) -> dict[str, int]:
    inferencer = AutoInferencer(backend="hybrid")
    counts: Counter[str] = Counter()

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        try:
            ft = inferencer.infer(file_path)
            ext = ft.extensions[0] if ft.extensions else "unknown"
            counts[ext] += 1
        except Exception:
            counts["unknown"] += 1

    return dict(counts)
```

## Parallelize Only When It Helps

Parallel processing can improve throughput when file I/O dominates.
Start simple first, then benchmark before you add concurrency.

```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from filetype_detector import AutoInferencer, FileType


def detect_type(file_path: Path) -> tuple[str, FileType | str]:
    inferencer = AutoInferencer(backend="hybrid")
    try:
        return (str(file_path), inferencer.infer(file_path))
    except Exception as exc:
        return (str(file_path), f"ERROR: {exc}")


with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(detect_type, file_list))
```

If you need better concurrency behavior, keep one inferencer per worker instead of creating one per file.

See [Examples and Patterns](../user-guide.md) for more batch-processing examples.