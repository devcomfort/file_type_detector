# User Guide

Comprehensive guide to using `file-type-infer` effectively.

## Overview

`file-type-infer` provides four different inferencers, each optimized for different use cases:

1. **LexicalInferencer**: Fastest, extension-based
2. **MagicInferencer**: Content-based using magic numbers
3. **MagikaInferencer**: AI-powered with confidence scores
4. **CascadingInferencer**: Hybrid approach (recommended)

## LexicalInferencer

The fastest inferencer, extracts file extensions directly from file paths without reading file contents.

### When to Use

- File extensions are known to be accurate
- Maximum performance is required
- No file I/O is acceptable

### Example

```python
from file_type_infer.lexical_inferencer import LexicalInferencer

inferencer = LexicalInferencer()

# Standard usage
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
extension = inferencer.infer("data.txt")      # Returns: '.txt'

# No extension
extension = inferencer.infer("file_without_ext")  # Returns: ''

# Case insensitive
extension = inferencer.infer("FILE.PDF")  # Returns: '.pdf'
```

### Limitations

- Cannot detect incorrect extensions
- Cannot detect files without extensions
- Returns empty string for files without extensions

## MagicInferencer

Uses `python-magic` (libmagic) to detect file types based on magic numbers and file signatures.

### System Requirements

Requires `libmagic` system library. See [Getting Started](getting-started.md#system-libraries) for installation instructions.

### When to Use

- Files may have incorrect or missing extensions
- Working with binary files
- Need content-based detection without AI overhead

### Example

```python
from file_type_infer.magic_inferencer import MagicInferencer
from pathlib import Path

inferencer = MagicInferencer()

# Standard usage
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'

# File with wrong extension
extension = inferencer.infer("data.txt")  # Returns: '.json' if it's actually JSON

# Using Path object
extension = inferencer.infer(Path("notes.txt"))  # Returns: '.txt'
```

### Error Handling

```python
from file_type_infer.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()

try:
    extension = inferencer.infer("nonexistent.pdf")
except FileNotFoundError:
    print("File not found")
except ValueError:
    print("Path is not a file")
except RuntimeError as e:
    print(f"Detection failed: {e}")
```

## MagikaInferencer

Uses Google's Magika AI model for advanced file type detection, especially effective for text files.

### When to Use

- Highest accuracy required
- Working primarily with text files
- Need confidence scores
- Detecting specific text file types (Python, JavaScript, JSON, etc.)

### Example

```python
from file_type_infer.magika_inferencer import MagikaInferencer
from magika import PredictionMode

inferencer = MagikaInferencer()

# Get extension only
extension = inferencer.infer("script.py")  # Returns: '.py'

# Get extension with confidence score
extension, score = inferencer.infer_with_score("data.json")
print(f"Extension: {extension}, Confidence: {score:.2%}")  
# Output: Extension: .json, Confidence: 95.00%

# Custom prediction mode
extension, score = inferencer.infer_with_score(
    "file.txt",
    prediction_mode=PredictionMode.HIGH_CONFIDENCE
)
```

### Prediction Modes

- `PredictionMode.MEDIUM_CONFIDENCE` (default): Balanced speed and accuracy
- `PredictionMode.HIGH_CONFIDENCE`: Higher accuracy, slightly slower
- `PredictionMode.BEST_GUESS`: Fastest, lower threshold

## CascadingInferencer

A two-stage inference strategy that combines Magic and Magika intelligently.

### System Requirements

Requires `libmagic` system library. See [Getting Started](getting-started.md#system-libraries) for installation instructions.

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
from file_type_infer.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()

# Text file - uses Magic then Magika
extension = inferencer.infer("script.py")  # Returns: '.py' (from Magika)

# Binary file - uses Magic only
extension = inferencer.infer("document.pdf")  # Returns: '.pdf' (from Magic)

# JSON with wrong extension
extension = inferencer.infer("data.txt")  # Returns: '.json' (from Magika)
```

## Using the Inferencer Map

The `FILE_FORMAT_INFERENCER_MAP` provides a centralized way to access inferencers:

```python
from file_type_infer.inferencer import FILE_FORMAT_INFERENCER_MAP, InferencerType

# Type-safe selection
def get_inferencer(method: InferencerType):
    return FILE_FORMAT_INFERENCER_MAP[method]

# Use it
magic_infer = get_inferencer("magic")
extension = magic_infer("file.pdf")
```

## Handling Different Input Types

All inferencers support both `Path` objects and strings:

```python
from pathlib import Path

inferencer = MagicInferencer()

# String path
extension1 = inferencer.infer("document.pdf")

# Path object
extension2 = inferencer.infer(Path("document.pdf"))

# Both return the same result
assert extension1 == extension2
```

## Best Practices

1. **Use CascadingInferencer by default** - Best balance of performance and accuracy
2. **Handle exceptions** - Always wrap inference calls in try-except blocks
3. **Check for empty strings** - LexicalInferencer can return empty strings
4. **Use confidence scores** - For MagikaInferencer, use `infer_with_score()` when accuracy matters
5. **Cache inferencer instances** - Reuse inferencer instances when processing multiple files

## Common Patterns

### Processing Multiple Files

```python
from file_type_infer.mixture_inferencer import CascadingInferencer
from pathlib import Path

inferencer = CascadingInferencer()

def process_directory(directory: Path):
    results = {}
    for file_path in directory.iterdir():
        if file_path.is_file():
            try:
                extension = inferencer.infer(file_path)
                results[file_path.name] = extension
            except Exception as e:
                results[file_path.name] = f"Error: {e}"
    return results
```

### Type-Safe File Processing

```python
from file_type_infer.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP

def process_with_method(file_path: str, method: InferencerType) -> str:
    inferencer_func = FILE_FORMAT_INFERENCER_MAP[method]
    try:
        return inferencer_func(file_path)
    except Exception as e:
        return f"Error: {e}"
```

