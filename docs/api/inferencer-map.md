# Inferencer Map

Centralized mapping for accessing inferencers by type-safe keys.

```python
from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP, InferencerType
```

## Overview

The `FILE_FORMAT_INFERENCER_MAP` provides a centralized dictionary that maps inferencer type keys to their corresponding inference functions. This allows easy switching between different file type detection strategies using simple string keys or `None`.

## Type Definition

```python
InferencerType = Union[Literal["magika", "magic"], None]
```

Available inference methods:
- `None`: Lexical inferencer (extension-based)
- `"magic"`: Magic inferencer (libmagic-based)
- `"magika"`: Magika inferencer (AI-powered)

## Inferencer Map

```python
FILE_FORMAT_INFERENCER_MAP: dict[InferencerType, Callable[[Union[Path, str]], str]] = {
    None: lambda path: LexicalInferencer().infer(path),
    "magic": lambda path: MagicInferencer().infer(path),
    "magika": lambda path: MagikaInferencer().infer(path),
}
```

## Usage Examples

### Basic Usage

```python
from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP

# Get lexical inferencer
lexical = FILE_FORMAT_INFERENCER_MAP[None]
extension = lexical("document.pdf")  # Returns: '.pdf'

# Get magic inferencer
magic = FILE_FORMAT_INFERENCER_MAP["magic"]
extension = magic("file_without_ext")  # Returns detected type

# Get magika inferencer
magika = FILE_FORMAT_INFERENCER_MAP["magika"]
extension = magika("script.py")  # Returns: '.py'
```

### Type-Safe Usage

```python
from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP

def process_file(file_path: str, method: InferencerType) -> str:
    """Process file with type-safe method selection."""
    inferencer_func = FILE_FORMAT_INFERENCER_MAP[method]
    return inferencer_func(file_path)

# Type-safe calls
result1 = process_file("doc.pdf", "magic")    # ✅ Valid
result2 = process_file("doc.pdf", None)       # ✅ Valid
result3 = process_file("doc.pdf", "magika")   # ✅ Valid
# result4 = process_file("doc.pdf", "invalid") # ❌ Type error
```

### Dynamic Method Selection

```python
from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP

def get_best_inferencer(file_type: str) -> InferencerType:
    """Select inferencer based on file type."""
    if file_type == "text":
        return "magika"  # Best for text files
    elif file_type == "binary":
        return "magic"   # Good for binary files
    else:
        return None      # Fastest for trusted extensions

method = get_best_inferencer("text")
inferencer = FILE_FORMAT_INFERENCER_MAP[method]
extension = inferencer("file.txt")
```

### Configuration-Based Selection

```python
from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP
from typing import Optional

class FileTypeDetector:
    """Configurable file type detector."""
    
    def __init__(self, method: Optional[str] = None):
        if method is None:
            method = "magic"  # Default
        self.method: InferencerType = method
        self.inferencer = FILE_FORMAT_INFERENCER_MAP[self.method]
    
    def detect(self, file_path: str) -> str:
        """Detect file type using configured method."""
        return self.inferencer(file_path)

# Usage
detector = FileTypeDetector(method="magic")
extension = detector.detect("file.pdf")
```

## Available Keys

### `None` - Lexical Inferencer

Fastest method that extracts file extensions from paths.

```python
lexical = FILE_FORMAT_INFERENCER_MAP[None]
extension = lexical("document.pdf")  # Returns: '.pdf'
```

**Characteristics:**
- Speed: Fastest
- I/O: None
- Accuracy: Low (extension-based only)

### `"magic"` - Magic Inferencer

Content-based detection using libmagic.

```python
magic = FILE_FORMAT_INFERENCER_MAP["magic"]
extension = magic("file_without_ext")  # Returns detected type
```

**Characteristics:**
- Speed: Fast
- I/O: File header read
- Accuracy: High for content-based detection

### `"magika"` - Magika Inferencer

AI-powered detection with confidence scores.

```python
magika = FILE_FORMAT_INFERENCER_MAP["magika"]
extension = magika("script.py")  # Returns: '.py'
```

**Note**: The map returns a function that uses `MagikaInferencer().infer()`, which doesn't return confidence scores. For scores, use `MagikaInferencer` directly.

**Characteristics:**
- Speed: Slower
- I/O: File content read
- Accuracy: Highest (especially for text files)

## Type Safety

The `InferencerType` ensures type safety:

```python
from filetype_detector.inferencer import InferencerType

# Valid types
method1: InferencerType = "magic"    # ✅
method2: InferencerType = "magika"   # ✅
method3: InferencerType = None       # ✅

# Invalid types (type errors)
# method4: InferencerType = "invalid"  # ❌
# method5: InferencerType = "lexical"  # ❌
```

## Best Practices

1. **Use type hints**: Leverage `InferencerType` for IDE support
2. **Reuse functions**: Get inferencer functions once, reuse for multiple files
3. **Handle exceptions**: All inferencers may raise exceptions
4. **Consider direct usage**: For Magika confidence scores, use `MagikaInferencer` directly

## Limitations

1. **Magika scores**: Map doesn't support confidence scores (use `MagikaInferencer` directly)
2. **New instances**: Each call creates new inferencer instance (consider caching)
3. **CascadingInferencer**: Not included in map (use directly)

## Integration Patterns

### With Configuration Files

```python
import json
from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP

# config.json: {"inference_method": "magic"}
with open("config.json") as f:
    config = json.load(f)

method: InferencerType = config.get("inference_method", "magic")
inferencer = FILE_FORMAT_INFERENCER_MAP[method]
```

### With Command-Line Arguments

```python
import argparse
from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP

parser = argparse.ArgumentParser()
parser.add_argument(
    "--method",
    choices=["magic", "magika"],
    default="magic",
    help="Inference method"
)
args = parser.parse_args()

method: InferencerType = args.method if args.method else None
inferencer = FILE_FORMAT_INFERENCER_MAP[method]
```

