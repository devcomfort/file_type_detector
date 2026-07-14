# Examples and Patterns

This page collects reusable examples, performance patterns, and integration snippets.
Use the [How-to Guides](how-to/index.md) for focused tasks and the [Reference Overview](reference/index.md) for exact API details.

## Overview

`filetype-detector` provides four different inferencers, each optimized for different use cases:

1. **LexicalInferencer**: Fastest, extension-based
2. **MagicInferencer**: Content-based using magic numbers
3. **MagikaInferencer**: AI-powered with confidence scores
4. **HybridInferencer**: Hybrid approach (recommended)

## LexicalInferencer

The fastest inferencer, extracts file extensions directly from file paths without reading file contents.

### When to Use

- File extensions are known to be accurate
- Maximum performance is required
- No file I/O is acceptable

### Example

```python
from filetype_detector import LexicalInferencer

inferencer = LexicalInferencer()
file_type = inferencer.infer("document.pdf")
file_type.extensions  # ('.pdf',)
inferencer.infer("file_without_ext")  # Raises ValueError
```

### Limitations

- Cannot detect incorrect extensions
- Cannot detect files without extensions
- Raises `ValueError` for paths without an extension

See [LexicalInferencer API](api/lexical_inferencer.md) for complete documentation.

## MagicInferencer

Uses `python-magic` (libmagic) to detect file types based on magic numbers and file signatures.

### System Requirements

Requires `libmagic` system library. See [Getting Started](getting-started.md#system-requirements) for installation instructions.

### When to Use

- Files may have incorrect or missing extensions
- Working with binary files
- Need content-based detection without AI overhead

### Example

```python
from filetype_detector import MagicInferencer

inferencer = MagicInferencer()
pdf_type = inferencer.infer("document.pdf")
'.pdf' in pdf_type.extensions  # True
json_type = inferencer.infer("data.txt")
'.json' in json_type.extensions  # True if the content is JSON
```

See [MagicInferencer API](api/magic_inferencer.md) for complete documentation including error handling.

## MagikaInferencer

Uses Google's Magika AI model for advanced file type detection, especially effective for text files.

### When to Use

- Highest accuracy required
- Working primarily with text files
- Need confidence scores
- Detecting specific text file types (Python, JavaScript, JSON, etc.)

### Example

```python
from filetype_detector import MagikaInferencer

inferencer = MagikaInferencer()
file_type = inferencer.infer("script.py")
'.py' in file_type.extensions  # True

# With confidence score
extension, score = inferencer.infer_with_score("data.json")
print(f"Extension: {extension}, Confidence: {score:.2%}")
```

See [MagikaInferencer API](api/magika_inferencer.md) for complete documentation including prediction modes.

## HybridInferencer

A two-stage inference strategy that combines Magic and Magika intelligently.

### System Requirements

Requires `libmagic` system library. See [Getting Started](getting-started.md#system-requirements) for installation instructions.

### How It Works

1. **Stage 1**: Uses Magic to detect MIME type
2. **Stage 2**: If detected as `text/*`, uses Magika for detailed type detection
3. **Fallback**: If Magika fails, falls back to Magic result

### When to Use

- **Recommended default** for most use cases
- Need balance between performance and accuracy
- Working with mixed file types (both binary and text)
- Want best of both worlds

### Example

```python
from filetype_detector import HybridInferencer

inferencer = HybridInferencer()

# Text file - uses Magic then Magika
text_type = inferencer.infer("script.py")
'.py' in text_type.extensions  # True

# Binary file - uses Magic only
binary_type = inferencer.infer("document.pdf")
'.pdf' in binary_type.extensions  # True
```

See [HybridInferencer API](api/hybrid_inferencer.md) for complete documentation.

## Using AutoInferencer

For type-safe backend selection, use `AutoInferencer`. See [AutoInferencer](api/auto_inferencer.md) for detailed usage patterns.

## Handling Different Input Types

All inferencers support both `Path` objects and strings:

```python
from pathlib import Path

inferencer = MagicInferencer()

# String path
file_type_from_string = inferencer.infer("document.pdf")

# Path object
file_type_from_path = inferencer.infer(Path("document.pdf"))

# Both return the same result
assert file_type_from_string == file_type_from_path
```

## Best Practices

1. **Use HybridInferencer by default** - Best balance of performance and accuracy
2. **Handle exceptions** - Always wrap inference calls in try-except blocks
3. **Handle missing suffixes** - LexicalInferencer raises `ValueError` when no extension is present
4. **Use confidence scores** - For MagikaInferencer, use `infer_with_score()` when accuracy matters
5. **Cache inferencer instances** - Reuse inferencer instances when processing multiple files

## Performance

### Quick Reference

| Inferencer | Avg. Time (per file) | Memory | Throughput | Best For |
|------------|---------------------|--------|------------|----------|
| LexicalInferencer | < 0.001ms | Minimal | 50,000+ files/sec | Trusted extensions |
| MagicInferencer | ~1-5ms | Low | 200-500 files/sec | Content-based detection |
| MagikaInferencer | ~5-10ms* | High** | 100-200 files/sec | Highest accuracy (text) |
| HybridInferencer | ~1-6ms | Medium | 150-400 files/sec | **Recommended default** |

\* After initial model load (~100-200ms one-time overhead)  
\*\* Model loaded into memory (~50-100MB)

### Optimization Strategies

#### 1. Reuse Inferencer Instances

**Bad:**
```python
for file_path in files:
    inferencer = MagicInferencer()  # Creates new instance each time
    file_type = inferencer.infer(file_path)
```

**Good:**
```python
inferencer = MagicInferencer()  # Create once
for file_path in files:
    file_type = inferencer.infer(file_path)
```

#### 2. Choose the Right Inferencer

**For high-volume processing with trusted extensions:**
```python
from filetype_detector import LexicalInferencer
inferencer = LexicalInferencer()  # Fastest
```

**For content-based detection:**
```python
from filetype_detector import MagicInferencer
inferencer = MagicInferencer()  # Good balance
```

**For mixed content (recommended):**
```python
from filetype_detector import HybridInferencer
inferencer = HybridInferencer()  # Optimizes automatically
```

#### 3. Batch Processing

For large batches, consider parallel processing:

```python
from concurrent.futures import ThreadPoolExecutor
from filetype_detector import FileType, HybridInferencer
from pathlib import Path

def detect_type(file_path: Path) -> tuple[str, FileType | str]:
    inferencer = HybridInferencer()
    try:
        file_type = inferencer.infer(file_path)
        return (str(file_path), file_type)
    except Exception as e:
        return (str(file_path), f"Error: {e}")

# Parallel processing
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(detect_type, file_list))
```

#### 4. Memory Considerations

The Magika model is loaded lazily on the first inference that needs it:
- **Model Size**: ~50-100MB
- **Load Time**: ~100-200ms (one-time)
- **Best Practice**: Create one MagikaInferencer instance and reuse it

#### 5. Caching Strategies

For repeated file type detection, consider caching:

```python
from functools import lru_cache
from filetype_detector import MagicInferencer

class CachedMagicInferencer(MagicInferencer):
    @lru_cache(maxsize=1000)
    def infer(self, file_path):
        return super().infer(str(file_path) if not isinstance(file_path, str) else file_path)

inferencer = CachedMagicInferencer()
# Subsequent calls with same file path use cache
```

For detailed performance characteristics of each inferencer, see the [BaseInferencer API](api/base_inferencer.md).

## Examples

### Batch Processing with Error Handling

```python
from filetype_detector import FileType, HybridInferencer
from pathlib import Path
from typing import Dict

def batch_detect(file_paths: list[Path]) -> dict[str, FileType | str]:
    """Detect file types for multiple files."""
    inferencer = HybridInferencer()
    results: dict[str, FileType | str] = {}
    
    for file_path in file_paths:
        try:
            file_type = inferencer.infer(file_path)
            results[str(file_path)] = file_type
        except FileNotFoundError:
            results[str(file_path)] = "ERROR: File not found"
        except ValueError:
            results[str(file_path)] = "ERROR: Not a file"
        except RuntimeError as e:
            results[str(file_path)] = f"ERROR: {e}"
    
    return results

# Usage
files = [Path("doc1.pdf"), Path("script.py"), Path("data.json")]
results = batch_detect(files)
for file, result in results.items():
    print(f"{file}: {result}")
```

### File Type Validator

```python
from filetype_detector import MagicInferencer
from pathlib import Path

def validate_file_type(file_path: Path, expected_extension: str) -> bool:
    """Validate that file matches expected type."""
    inferencer = MagicInferencer()
    try:
        detected = inferencer.infer(file_path)
        return expected_extension in detected.extensions
    except Exception:
        return False

# Usage
is_pdf = validate_file_type(Path("document.pdf"), ".pdf")
print(f"Is PDF: {is_pdf}")  # Output: Is PDF: True
```

### Confidence-Based Filtering

```python
from filetype_detector import MagikaInferencer
from magika import PredictionMode
from pathlib import Path

def filter_by_confidence(
    file_path: Path, 
    min_confidence: float = 0.9
) -> tuple[str, float] | None:
    """Get file type only if confidence meets threshold."""
    inferencer = MagikaInferencer()
    extension, score = inferencer.infer_with_score(
        file_path, 
        prediction_mode=PredictionMode.HIGH_CONFIDENCE
    )
    
    if score >= min_confidence:
        return (extension, score)
    return None

# Usage
result = filter_by_confidence(Path("script.py"), min_confidence=0.9)
if result:
    ext, conf = result
    print(f"High confidence: {ext} ({conf:.2%})")
```

### Directory Scanner

```python
from filetype_detector import HybridInferencer
from pathlib import Path
from collections import Counter

def scan_directory(directory: Path) -> dict[str, int]:
    """Scan directory and count file types."""
    inferencer = HybridInferencer()
    type_counts = Counter()
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                file_type = inferencer.infer(file_path)
                extension = file_type.extensions[0] if file_type.extensions else "unknown"
                type_counts[extension] += 1
            except Exception:
                type_counts["unknown"] += 1
    
    return dict(type_counts)

# Usage
stats = scan_directory(Path("./documents"))
for ext, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"{ext}: {count} files")
```

### Custom Inferencer Chain

```python
from filetype_detector import FileType, LexicalInferencer, MagicInferencer
from pathlib import Path

def infer_with_fallback(file_path: Path) -> FileType:
    """Use content detection when the path does not have an extension."""
    lexical = LexicalInferencer()
    try:
        return lexical.infer(file_path)
    except ValueError:
        return MagicInferencer().infer(file_path)

# Usage
result = infer_with_fallback(Path("file_without_ext"))
print(f"Detected: {result}")
```

### Type-Safe File Router

```python
from filetype_detector import AutoInferencer, BackendType
from pathlib import Path
from typing import Callable

class FileRouter:
    """Route files based on type."""
    
    def __init__(self, backend: BackendType = "magic"):
        self.inferencer = AutoInferencer(backend=backend)
        self.handlers: dict[str, Callable] = {}
    
    def register(self, extension: str, handler: Callable):
        """Register a handler for an extension."""
        self.handlers[extension] = handler
    
    def route(self, file_path: Path):
        """Route file to appropriate handler."""
        file_type = self.inferencer.infer(file_path)
        for extension in file_type.extensions:
            handler = self.handlers.get(extension)
            if handler:
                return handler(file_path)
        return None

# Usage
router = FileRouter(backend="magic")
router.register(".pdf", lambda p: print(f"Processing PDF: {p}"))
router.register(".py", lambda p: print(f"Processing Python: {p}"))

router.route(Path("document.pdf"))  # Output: Processing PDF: document.pdf
router.route(Path("script.py"))     # Output: Processing Python: script.py
```

### Integration Examples

#### With Pandas

```python
import pandas as pd
from filetype_detector import HybridInferencer
from pathlib import Path

def create_file_type_dataframe(directory: Path) -> pd.DataFrame:
    """Create DataFrame with file type information."""
    inferencer = HybridInferencer()
    data = []
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                file_type = inferencer.infer(file_path)
                data.append({
                    "file": file_path.name,
                    "path": str(file_path),
                    "extension": file_type.extensions[0] if file_type.extensions else None,
                    "size": file_path.stat().st_size
                })
            except Exception:
                pass
    
    return pd.DataFrame(data)

# Usage
df = create_file_type_dataframe(Path("./documents"))
print(df.groupby("extension").size())
```

#### With FastAPI

```python
from fastapi import FastAPI, HTTPException
from filetype_detector import HybridInferencer
from pathlib import Path

app = FastAPI()
inferencer = HybridInferencer()

@app.post("/detect/{file_path:path}")
async def detect_file_type(file_path: str):
    """API endpoint for file type detection."""
    try:
        file_type = inferencer.infer(file_path)
        return {
            "file": file_path,
            "extensions": file_type.extensions,
            "mime_types": file_type.mime_types,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

