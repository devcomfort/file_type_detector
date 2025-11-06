# CascadingInferencer

Smart two-stage inference that combines Magic and Magika for optimal performance and accuracy.

```python
from filetype_detector.mixture_inferencer import CascadingInferencer
```

## Overview

The `CascadingInferencer` implements an intelligent two-stage inference strategy:

1. **Stage 1**: Uses Magic (libmagic) to detect MIME type for all files
2. **Stage 2**: If detected as a text file (`text/*` MIME type), uses Magika for detailed type detection
3. **Fallback**: If Magika fails, falls back to Magic result

This approach optimizes performance by only using Magika (computationally expensive) for text files where it excels, while using faster Magic detection for binary files.

## Class Definition

```python
class CascadingInferencer(BaseInferencer):
    """Cascading inferencer that combines magic and magika inference methods."""
```

## Methods

### `infer(file_path: Union[Path, str]) -> str`

Infer the file format using a cascading two-stage approach.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file to analyze. Can be a string or `Path` object.

**Returns:**

- `str`: File extension with leading dot (e.g., `'.pdf'`, `'.txt'`, `'.py'`, `'.json'`). For text files, returns the more specific type detected by Magika when available.

**Raises:**

- `FileNotFoundError`: If the file does not exist.
- `ValueError`: If the path is not a file.
- `RuntimeError`: If MIME type cannot be determined or Magika fails to analyze the file.

**Examples:**

```python
from filetype_detector.mixture_inferencer import CascadingInferencer
from pathlib import Path

inferencer = CascadingInferencer()

# Text file - uses Magic then Magika
extension = inferencer.infer('script.py')  # Returns: '.py'

# Binary file - uses Magic only
extension = inferencer.infer('document.pdf')  # Returns: '.pdf'

# JSON with wrong extension
extension = inferencer.infer('data.txt')  # May return: '.json'
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
from filetype_detector.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()

# Text file - automatically uses Magika
extension = inferencer.infer("script.py")  # Returns: '.py'

# Binary file - uses Magic only
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
```

### Mixed File Types

```python
inferencer = CascadingInferencer()

files = [
    "document.pdf",   # Binary - Magic only
    "script.py",      # Text - Magic + Magika
    "data.json",      # Text - Magic + Magika
    "image.png",      # Binary - Magic only
]

for file_path in files:
    extension = inferencer.infer(file_path)
    print(f"{file_path}: {extension}")
```

### Error Handling

```python
from filetype_detector.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()

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

### Text Files
- **Magic detection**: ~1-5ms
- **Magika detection**: ~5-10ms
- **Total**: ~6-15ms per file

### Binary Files
- **Magic detection only**: ~1-5ms
- **Total**: ~1-5ms per file

### Overall Throughput
- **Mixed content**: 150-400 files/second (depends on text/binary ratio)
- **Text-heavy**: 100-200 files/second
- **Binary-heavy**: 200-500 files/second

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

| Aspect | CascadingInferencer | MagicInferencer | MagikaInferencer |
|--------|-------------------|-----------------|------------------|
| Text file accuracy | Highest (via Magika) | Medium | Highest |
| Binary file accuracy | High (via Magic) | High | High |
| Speed (text) | Medium | Fast | Slower |
| Speed (binary) | Fast | Fast | Slower |
| Memory | Medium | Low | High |
| Use case | **Recommended default** | Binary-focused | Text-focused |

## Benefits

1. **Intelligent routing**: Automatically chooses best method per file type
2. **Performance optimized**: Only uses expensive Magika for text files
3. **Best accuracy**: Combines strengths of both methods
4. **Robust fallback**: Handles Magika failures gracefully
5. **Single interface**: One inferencer for all use cases

## System Requirements

`CascadingInferencer` requires both `libmagic` (system library) and `magika` (Python package).

### libmagic Installation

Install `libmagic` based on your operating system:

- **Ubuntu/Debian**: `sudo apt-get install libmagic1`
- **Fedora/RHEL/CentOS**: `sudo dnf install file-libs` (or `sudo yum install file-libs`)
- **Arch Linux**: `sudo pacman -S file`
- **macOS**: `brew install libmagic` or `sudo port install file`
- **Windows**: `pip install python-magic-bin`
- **Alpine Linux**: `apk add --no-cache file`

See [MagicInferencer System Requirements](magic.md#system-requirements) for detailed installation instructions.

### magika Installation

`magika` is installed automatically with the Python package. No additional system dependencies required.

## Limitations

1. **Model load**: Magika model still loaded into memory (even if not used)
2. **Slightly slower**: For pure binary workflows, MagicInferencer is faster
3. **Two dependencies**: Requires both python-magic (libmagic) and magika

## Best Practices

1. **Reuse instance**: Create one CascadingInferencer and reuse it
2. **Handle exceptions**: Always wrap in try-except blocks
3. **Monitor performance**: Profile if processing very large batches
4. **Consider alternatives**: For pure binary/text workflows, consider specialized inferencers

