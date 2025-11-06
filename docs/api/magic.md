# MagicInferencer

Content-based file type detection using python-magic (libmagic).

```python
from filetype_detector.magic_inferencer import MagicInferencer
```

## Overview

The `MagicInferencer` uses `python-magic`, which provides Python bindings for the `libmagic` library. It detects file types based on magic numbers and file signatures, making it reliable for files with incorrect or missing extensions.

## Class Definition

```python
class MagicInferencer(BaseInferencer):
    """Magic inferencer that uses python-magic to infer the file format."""
```

## Methods

### `infer(file_path: Union[Path, str]) -> str`

Infer file extension using python-magic and mimetypes.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file to analyze. Can be a string or `Path` object.

**Returns:**

- `str`: File extension with leading dot (e.g., `'.pdf'`, `'.txt'`). Never returns an empty string as `RuntimeError` is raised if the MIME type cannot be converted to an extension.

**Raises:**

- `FileNotFoundError`: If the file does not exist.
- `ValueError`: If the path is not a file.
- `RuntimeError`: If the MIME type cannot be determined or converted to an extension.

**Examples:**

```python
from filetype_detector.magic_inferencer import MagicInferencer
from pathlib import Path

inferencer = MagicInferencer()

# String path
extension = inferencer.infer('document.pdf')  # Returns: '.pdf'

# Path object
extension = inferencer.infer(Path('notes.txt'))  # Returns: '.txt'
```

## Usage Examples

### Basic Usage

```python
from filetype_detector.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()
extension = inferencer.infer("document.pdf")
print(extension)  # Output: '.pdf'
```

### Detecting Files with Wrong Extensions

```python
inferencer = MagicInferencer()

# File named .txt but contains JSON
extension = inferencer.infer("data.txt")  # May return: '.json'

# File without extension
extension = inferencer.infer("file_without_ext")  # Returns detected type
```

### Error Handling

```python
from filetype_detector.magic_inferencer import MagicInferencer

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

## How It Works

1. **File Validation**: Checks if file exists and is accessible
2. **MIME Type Detection**: Uses `python-magic` to detect MIME type from file content
3. **Extension Conversion**: Converts MIME type to file extension using `mimetypes` module

## Performance

- **Speed**: Fast (~1-5ms per file)
- **I/O**: Reads file headers (first few KB)
- **Memory**: Low
- **Throughput**: 200-500 files/second

See [User Guide](../user-guide.md#performance) for optimization tips.

## When to Use

✅ **Good for:**
- Files with incorrect or missing extensions
- Content-based file type detection
- Binary file type detection
- General-purpose file type detection
- When AI-level accuracy isn't required

❌ **Not suitable for:**
- Maximum performance requirements (use LexicalInferencer)
- Detailed text file type detection (use MagikaInferencer)
- When you need confidence scores (use MagikaInferencer)

## System Requirements

The `MagicInferencer` requires the `libmagic` system library. See [Getting Started](../getting-started.md#system-requirements) for installation instructions.

## Limitations

1. **MIME type conversion**: Some MIME types may not map to extensions cleanly
2. **Text file specificity**: May return generic `text/plain` for various text files
3. **Performance**: Slower than lexical inference due to file I/O

## Common MIME Types

The inferencer handles various MIME types:

- `application/pdf` → `.pdf`
- `text/plain` → `.txt`
- `application/json` → `.json`
- `text/x-python` → `.py`
- `image/png` → `.png`
- `application/zip` → `.zip`

## Best Practices

1. **Reuse instances**: Create one inferencer instance and reuse it for multiple files
2. **Handle exceptions**: Always wrap calls in try-except blocks
3. **Validate paths**: Ensure paths exist before calling (though inferencer will validate)

