# LexicalInferencer

Fastest inferencer that extracts file extensions directly from file paths.

```python
from filetype_detector import LexicalInferencer
```

## Overview

The `LexicalInferencer` is the fastest file type detection method, extracting file extensions directly from file paths without reading file contents. This makes it ideal for scenarios where file extensions are trusted or when maximum performance is required.

## Class Definition

```python
class LexicalInferencer(BaseInferencer):
    """Lexical inferencer that uses the file path to infer the file format."""
```

## Methods

### `infer(file_path: Union[Path, str]) -> FileType`

Infer the file format from the file path.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file. Can be a `Path` object or a string representing the file system path.

**Returns:**

- `FileType`: A frozen dataclass with `extensions` and `mime_types` tuples. Raises `ValueError` if the path has no extension.

**Examples:**

```python
from filetype_detector import LexicalInferencer
from pathlib import Path

inferencer = LexicalInferencer()

# String path
ft = inferencer.infer('document.pdf')
'.pdf' in ft.extensions  # True

# Path object
ft = inferencer.infer(Path('data.txt'))
'.txt' in ft.extensions  # True

# No extension
inferencer.infer('no_extension')  # Raises ValueError
```

## Usage Examples

### Basic Usage

```python
from filetype_detector import LexicalInferencer

inferencer = LexicalInferencer()
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions  # True
ft.mime_types             # ('application/pdf',)
```

### Case Insensitive

The inferencer automatically converts extensions to lowercase:

```python
inferencer = LexicalInferencer()
ft1 = inferencer.infer("FILE.PDF")
ft2 = inferencer.infer("file.pdf")
'.pdf' in ft1.extensions  # True
'.pdf' in ft2.extensions  # True
```

### Multiple Dots

When filenames contain multiple dots, returns the last extension:

```python
inferencer = LexicalInferencer()
ft1 = inferencer.infer("file.tar.gz")
'.gz' in ft1.extensions   # True
```

### Files Without Extensions

Paths without a suffix are invalid lexical inputs:

```python
inferencer = LexicalInferencer()

try:
    inferencer.infer("no_extension")
except ValueError:
    print("No extension detected")

try:
    inferencer.infer(".hidden")
except ValueError:
    print("No extension detected")
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

1. **Cannot detect wrong extensions**: A file named `document.pdf` will return a `FileType` with `.pdf` even if it's actually a Word document
2. **Missing extension error**: Paths without extensions raise `ValueError`
3. **No content analysis**: Pure path-based detection only

## Error Handling

`LexicalInferencer` does not access the filesystem. It accepts path-like strings
whether or not the file exists, but raises `ValueError` when the path has no
extension.

```python
inferencer = LexicalInferencer()

try:
    file_type = inferencer.infer("file_without_ext")
except ValueError as error:
    print(error)
else:
    print(file_type.extensions)
```

