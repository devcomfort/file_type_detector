# HybridInferencer

Smart two-stage inference that combines Magic and Magika for optimal performance and accuracy.

```python
from filetype_detector import HybridInferencer
```

## Overview

The `HybridInferencer` implements an intelligent two-stage inference strategy:

1. **Stage 1**: Uses Magic (libmagic) to detect MIME type for all files
2. **Stage 2**: If detected as a text file (`text/*` MIME type), uses Magika for detailed type detection
3. **Fallback**: If Magika fails, falls back to Magic result

This approach optimizes performance by only using Magika (computationally expensive) for text files where it excels, while using faster Magic detection for binary files.

## Class Definition

```python
class HybridInferencer(BaseInferencer):
    """Hybrid inferencer that combines Magic and Magika."""
```

## Methods

### `infer(file_path: Union[Path, str]) -> FileType`

Infer the file format using a hybrid two-stage approach.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file to analyze. Can be a string or `Path` object.

**Returns:**

- `FileType`: A frozen dataclass with `extensions` and `mime_types` tuples. For text files, reflects the more specific type detected by Magika when available.

**Raises:**

- `FileNotFoundError`: If the file does not exist.
- `ValueError`: If the path is not a file.
- `RuntimeError`: If MIME type cannot be determined or Magika fails to analyze the file.

**Examples:**

```python
from filetype_detector import HybridInferencer
from pathlib import Path

inferencer = HybridInferencer()

# Text file: Magic detects text/plain, Magika refines to .py
ft = inferencer.infer('script.py')
'.py' in ft.extensions   # True

# Binary file: Magic result only
ft = inferencer.infer('document.pdf')
'.pdf' in ft.extensions  # True

# JSON data in a .txt file
ft = inferencer.infer('data.txt')  # Magika may return .json
```

## Inference Flow

```
File Input
    ↓
[Stage 1: Magic Detection]
    ↓
MIME Type Detection
    ↓
Is text/* MIME type?
    ├─ Yes → [Stage 2: Magika Detection]
    │         ↓
    │     Detailed Type Detection
    │         ↓
    │     Return Magika Result
    │         ↓
    │     (Fallback to Magic if Magika fails)
    │
    └─ No → Return Magic Result
```

## Usage Examples

### Basic Usage

```python
from filetype_detector import HybridInferencer

inferencer = HybridInferencer()

# Text file: automatically uses Magika
ft = inferencer.infer("script.py")
'.py' in ft.extensions   # True

# Binary file: uses Magic only
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions  # True
```

### Mixed File Types

```python
inferencer = HybridInferencer()

files = [
    "document.pdf",   # Binary - Magic only
    "script.py",      # Text - Magic + Magika
    "data.json",      # Text - Magic + Magika
    "image.png",      # Binary - Magic only
]

for file_path in files:
    ft = inferencer.infer(file_path)
    print(f"{file_path}: {ft.extensions}")
```

### Error Handling

```python
from filetype_detector import HybridInferencer

inferencer = HybridInferencer()

try:
    extension = inferencer.infer("nonexistent.pdf")
except FileNotFoundError:
    print("File not found")
except ValueError:
    print("Path is not a file")
except RuntimeError as e:
    print(f"Detection failed: {e}")
```

## How It Works

### Stage 1: Magic Detection

All files go through Magic (libmagic) first:

```python
# Magic detects MIME type
mime_type = magic.from_file(file_path_str, mime=True)
# Example: 'text/plain', 'application/pdf', etc.
```

### Stage 2: Magika for Text Files

If MIME type starts with `text/`, Magika is used:

```python
if mime_type.startswith("text/"):
    # Use Magika for detailed detection
    result = magika.identify_path(path=file_path_str)
    extension = result.output.extensions[0]  # Get first extension
    return extension
```

### Fallback Mechanism

If Magika fails or returns empty result, falls back to Magic:

```python
try:
    # Try Magika
    extension = magika_result
except Exception:
    # Fall back to Magic result
    pass

# Use Magic result
extension = mimetypes.guess_extension(mime_type)
```

## Performance Characteristics

- **Text files**: ~6-15ms per file (Magic + Magika)
- **Binary files**: ~1-5ms per file (Magic only)
- **Throughput**: 150-400 files/second (depends on text/binary ratio)

See [Examples and Patterns](../user-guide.md#performance) for detailed optimization strategies.

## When to Use

✅ **Recommended default** for most use cases:
- General-purpose file type detection
- Mixed content (both binary and text files)
- Need balance between performance and accuracy
- Want best of both worlds (Magic speed + Magika precision)

✅ **Especially good for:**
- Processing directories with mixed file types
- Applications requiring both speed and accuracy
- Text file workflows where specific types matter

❌ **Consider alternatives when:**
- Only processing binary files → Use `MagicInferencer`
- Maximum performance needed → Use `LexicalInferencer`
- Only text files, need confidence scores → Use `MagikaInferencer` directly

## Comparison

| Aspect               | HybridInferencer     | MagicInferencer | MagikaInferencer |
| -------------------- | ----------------------- | --------------- | ---------------- |
| Text file accuracy   | Highest (via Magika)    | Medium          | Highest          |
| Binary file accuracy | High (via Magic)        | High            | High             |
| Speed (text)         | Medium                  | Fast            | Slower           |
| Speed (binary)       | Fast                    | Fast            | Slower           |
| Memory               | Medium                  | Low             | High             |
| Use case             | **Recommended default** | Binary-focused  | Text-focused     |

## Benefits

1. **Intelligent routing**: Automatically chooses best method per file type
2. **Performance optimized**: Only uses expensive Magika for text files
3. **Best accuracy**: Combines strengths of both methods

## Known Limitations

- **ZIP-based formats**: HWPX, ODF, ePub, and other ZIP-wrapped formats are detected as `text/...` only if the ZIP happens to unpack as text, which is unlikely. They fall through to Magic and are returned as `application/zip`. Magika is not applied.
- **HWP**: Magic correctly identifies HWP; Magika is not called for binary files, so this works correctly via the Magic path.
- **Compound Document formats**: Legacy Office formats (`.doc`, `.ppt`, `.xls`) are binary, so Magic handles them. Multiple extensions may appear in `ft.extensions` because the MIME type is shared across formats.
- **Magika only helps for `text/*`**: Files that Magic classifies as binary are never sent to Magika, even if Magika could provide a more specific label.
4. **Robust fallback**: Handles Magika failures gracefully
5. **Single interface**: One inferencer for all use cases

## System Requirements

`HybridInferencer` requires both `libmagic` (system library) and `magika` (Python package). See [Getting Started](../getting-started.md#system-requirements) for installation instructions.

## Limitations

1. **Model load**: Magika model still loaded into memory (even if not used)
2. **Slightly slower**: For pure binary workflows, MagicInferencer is faster
3. **Two dependencies**: Requires both python-magic (libmagic) and magika

## Best Practices

1. **Reuse instance**: Create one HybridInferencer and reuse it
2. **Handle exceptions**: Always wrap in try-except blocks
3. **Monitor performance**: Profile if processing very large batches
4. **Consider alternatives**: For pure binary/text workflows, consider specialized inferencers

