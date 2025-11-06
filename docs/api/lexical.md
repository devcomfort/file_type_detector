# LexicalInferencer

Fastest inferencer that extracts file extensions directly from file paths.

```python
from filetype_detector.lexical_inferencer import LexicalInferencer
```

## Overview

The `LexicalInferencer` is the fastest file type detection method, extracting file extensions directly from file paths without reading file contents. This makes it ideal for scenarios where file extensions are trusted or when maximum performance is required.

## Class Definition

```python
class LexicalInferencer(BaseInferencer):
    """Lexical inferencer that uses the file path to infer the file format."""
```

## Methods

### `infer(file_path: Union[Path, str]) -> str`

Infer the file format from the file path.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file. Can be a `Path` object or a string representing the file system path.

**Returns:**

- `str`: File extension in lowercase with leading dot (e.g., `'.txt'`, `'.pdf'`). Returns an empty string if the file has no extension.

**Examples:**

```python
from filetype_detector.lexical_inferencer import LexicalInferencer
from pathlib import Path

inferencer = LexicalInferencer()

# String path
extension = inferencer.infer('document.pdf')  # Returns: '.pdf'

# Path object
extension = inferencer.infer(Path('data.txt'))  # Returns: '.txt'

# No extension
extension = inferencer.infer('no_extension')  # Returns: ''
```

## Usage Examples

### Basic Usage

```python
from filetype_detector.lexical_inferencer import LexicalInferencer

inferencer = LexicalInferencer()
extension = inferencer.infer("document.pdf")
print(extension)  # Output: '.pdf'
```

### Case Insensitive

The inferencer automatically converts extensions to lowercase:

```python
inferencer = LexicalInferencer()
extension1 = inferencer.infer("FILE.PDF")      # Returns: '.pdf'
extension2 = inferencer.infer("file.pdf")     # Returns: '.pdf'
extension3 = inferencer.infer("File.Pdf")     # Returns: '.pdf'
```

### Multiple Dots

When filenames contain multiple dots, returns the last extension:

```python
inferencer = LexicalInferencer()
extension1 = inferencer.infer("file.tar.gz")           # Returns: '.gz'
extension2 = inferencer.infer("backup.2024.01.01.txt") # Returns: '.txt'
```

### Files Without Extensions

```python
inferencer = LexicalInferencer()
extension1 = inferencer.infer("no_extension")  # Returns: ''
extension2 = inferencer.infer(".hidden")       # Returns: ''
extension3 = inferencer.infer("")               # Returns: ''
```

## Performance

- **Speed**: Fastest (~< 0.001ms per file)
- **I/O**: None (pure string manipulation)
- **Memory**: Minimal
- **Throughput**: 50,000+ files/second

## When to Use

✅ **Good for:**
- High-volume processing where extensions are trusted
- Maximum performance requirements
- Simple extension extraction without content analysis
- Cases where file I/O should be avoided

❌ **Not suitable for:**
- Detecting incorrect file extensions
- Files without extensions
- Content-based type detection
- Validating file types

## Limitations

1. **Cannot detect wrong extensions**: A file named `document.pdf` will return `'.pdf'` even if it's actually a Word document
2. **Returns empty string for no extension**: Files without extensions return `''`
3. **No content analysis**: Pure path-based detection only

## Error Handling

The `LexicalInferencer` does not raise exceptions (except for invalid input types). It will return an empty string for files without extensions, which should be handled by the caller.

```python
inferencer = LexicalInferencer()
extension = inferencer.infer("file_without_ext")

if not extension:
    # Handle files without extension
    print("No extension detected")
else:
    print(f"Extension: {extension}")
```

