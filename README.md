# filetype-detector

A Python library for detecting file types using multiple inference strategies, including path-based extraction, magic number detection, and AI-powered content analysis.

## Features

- **Multiple Inference Methods**: Choose from lexical, magic-based, AI-powered, or cascading inference strategies
- **Type-Safe API**: Type hints and type-safe inference method selection
- **Flexible Input**: Supports both `Path` objects and string paths
- **Performance Optimized**: Cascading inferencer intelligently combines methods for optimal performance
- **Well-Tested**: Comprehensive test suite with logging support
- **Extensible**: Base class architecture for custom inferencer implementations

## Installation

### Python Package

```bash
pip install filetype-detector
```

Or using rye:

```bash
rye sync
```

### System Dependencies

**Important**: `MagicInferencer` and `CascadingInferencer` require the `libmagic` system library to be installed.

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install libmagic1
```

#### Fedora/RHEL/CentOS

```bash
sudo dnf install file-libs
# or for older versions:
# sudo yum install file-libs
```

#### Arch Linux

```bash
sudo pacman -S file
```

#### macOS

Using Homebrew:

```bash
brew install libmagic
```

Using MacPorts:

```bash
sudo port install file
```

#### Windows

Windows users need to use `python-magic-bin` as an alternative:

```bash
pip install python-magic-bin
```

Or download `libmagic` DLL manually from [file.exe releases](https://github.com/julian-r/file-windows/releases).

#### Alpine Linux (Docker)

```bash
apk add --no-cache file
```

#### Verification

After installation, verify `libmagic` is available:

```bash
file --version
```

If the command works, `libmagic` is properly installed.

## Quick Start

### Using the Inferencer Map (Recommended)

The simplest way to use filetype-detector is through the centralized `FILE_FORMAT_INFERENCER_MAP`:

```python
from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP, InferencerType
from pathlib import Path

# Lexical inference (fastest, extension-based)
lexical_infer = FILE_FORMAT_INFERENCER_MAP[None]
extension = lexical_infer("document.pdf")  # Returns: '.pdf'

# Magic inference (content-based using magic numbers)
magic_infer = FILE_FORMAT_INFERENCER_MAP["magic"]
extension = magic_infer("file_without_ext")  # Returns: '.txt' (detected from content)

# Magika inference (AI-powered with confidence scores)
magika_infer = FILE_FORMAT_INFERENCER_MAP["magika"]
extension = magika_infer("script.py")  # Returns extension detected by AI
```

### Using Individual Inferencers

You can also use inferencer classes directly:

```python
from filetype_detector.lexical_inferencer import LexicalInferencer
from filetype_detector.magic_inferencer import MagicInferencer
from filetype_detector.magika_inferencer import MagikaInferencer
from filetype_detector.mixture_inferencer import CascadingInferencer

# Lexical inferencer - extracts extension from path
lexical = LexicalInferencer()
extension = lexical.infer("document.pdf")  # Returns: '.pdf'

# Magic inferencer - uses libmagic for content analysis
magic = MagicInferencer()
extension = magic.infer("file.dat")  # Returns actual type based on content

# Magika inferencer - AI-powered detection
magika = MagikaInferencer()
extension = magika.infer("script.py")  # Returns: '.py'

# Get confidence score (Magika only)
extension, score = magika.infer_with_score("data.json")  # Returns: ('.json', 0.98)

# Cascading inferencer - best of both worlds
cascading = CascadingInferencer()
extension = cascading.infer("data.txt")  # Uses Magic, then Magika for text files
```

## Available Inferencers

### 1. LexicalInferencer

Fastest method that extracts file extensions directly from file paths. No content analysis is performed.

**When to use**: When file extensions are known to be accurate or when you need maximum performance.

```python
from filetype_detector.lexical_inferencer import LexicalInferencer

inferencer = LexicalInferencer()
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
extension = inferencer.infer("file_without_ext")  # Returns: ''
```

### 2. MagicInferencer

Uses `python-magic` (libmagic) to detect file types based on magic numbers and file signatures. Reliable for files with incorrect or missing extensions.

**When to use**: When you need content-based detection but don't need AI-level accuracy, or when working with binary files.

```python
from filetype_detector.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()
extension = inferencer.infer("file.dat")  # May return: '.pdf' (detected from content)
```

**Raises**:
- `FileNotFoundError`: If the file does not exist
- `ValueError`: If the path is not a file
- `RuntimeError`: If MIME type cannot be determined or converted to an extension

### 3. MagikaInferencer

Uses Google's Magika AI model for advanced file type detection, especially effective for text files. Provides confidence scores and detailed type information.

**When to use**: When you need the highest accuracy, especially for text files, or when you need confidence scores.

```python
from filetype_detector.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()

# Get extension only
extension = inferencer.infer("script.py")  # Returns: '.py'

# Get extension with confidence score
extension, score = inferencer.infer_with_score("data.json")  
# Returns: ('.json', 0.98)

# With custom prediction mode
from magika import PredictionMode
extension, score = inferencer.infer_with_score(
    "file.txt", 
    prediction_mode=PredictionMode.HIGH_CONFIDENCE
)
```

**Raises**:
- `FileNotFoundError`: If the file does not exist
- `ValueError`: If the path is not a file
- `RuntimeError`: If Magika fails to analyze the file

### 4. CascadingInferencer (Recommended)

A smart two-stage inference strategy that combines Magic and Magika:

1. **Stage 1**: Uses Magic for all files (fast)
2. **Stage 2**: If detected as a text file (`text/*` MIME type), uses Magika for detailed type detection

This approach optimizes performance by only using Magika (computationally expensive) for text files where it excels, while using faster Magic detection for binary files.

**When to use**: Recommended default choice for balanced performance and accuracy.

**System Requirements**: Requires `libmagic` system library. See [Installation](#installation) section for OS-specific setup.

```python
from filetype_detector.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()

# Text file - uses Magic then Magika
extension = inferencer.infer("script.py")  # Returns: '.py' (from Magika)

# Binary file - uses Magic only
extension = inferencer.infer("document.pdf")  # Returns: '.pdf' (from Magic)

# JSON file with wrong extension
extension = inferencer.infer("data.txt")  # May return: '.json' (from Magika)
```

## Type-Safe Usage

The library provides type-safe inference method selection:

```python
from filetype_detector.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP

def process_file(file_path: str, method: InferencerType) -> str:
    inferencer_func = FILE_FORMAT_INFERENCER_MAP[method]
    extension = inferencer_func(file_path)
    return extension

# Type-safe calls
result1 = process_file("doc.pdf", "magic")      # ✅ Valid
result2 = process_file("doc.pdf", None)         # ✅ Valid
result3 = process_file("doc.pdf", "invalid")   # ❌ Type error
```

## Handling Edge Cases

### Files Without Extensions

```python
# Lexical inferencer returns empty string
lexical = LexicalInferencer()
result = lexical.infer("file_without_ext")  # Returns: ''

# Magic/Magika inferencers detect from content
magic = MagicInferencer()
result = magic.infer("file_without_ext")  # Returns: '.txt' (detected)

cascading = CascadingInferencer()
result = cascading.infer("file_without_ext")  # Returns detected extension
```

### Wrong File Extensions

```python
# File named 'data.txt' but contains JSON
magic = MagicInferencer()
result = magic.infer("data.txt")  # May return: '.json'

magika = MagikaInferencer()
result, score = magika.infer_with_score("data.txt")  # Returns: ('.json', 0.95)
```

## Error Handling

All inferencers raise appropriate exceptions:

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

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

With logging (using loguru):

```bash
pytest tests/ -v -s
```

Run specific test files:

```bash
pytest tests/test_cascading_inferencer.py -v
pytest tests/test_magic_inferencer.py -v
pytest tests/test_magika_inferencer.py -v
pytest tests/test_lexical_inferencer.py -v
```

## Architecture

### Base Class

All inferencers inherit from `BaseInferencer`, which defines a common interface:

```python
from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path

class BaseInferencer(ABC):
    @abstractmethod
    def infer(self, file_path: Union[Path, str]) -> str:
        """Infer file format from path."""
        raise NotImplementedError
```

### Custom Inferencer

You can create custom inferencers by subclassing `BaseInferencer`:

```python
from filetype_detector.base_inferencer import BaseInferencer
from typing import Union
from pathlib import Path

class CustomInferencer(BaseInferencer):
    def infer(self, file_path: Union[Path, str]) -> str:
        # Your custom logic here
        return ".custom"
```

## Performance Considerations

1. **LexicalInferencer**: Fastest (~microseconds), no I/O required
2. **MagicInferencer**: Fast (~milliseconds), requires file read
3. **MagikaInferencer**: Slower (~5-10ms after model load), requires file read + AI inference
4. **CascadingInferencer**: Balanced - Magic speed for binaries, Magika accuracy for text files

## Dependencies

- `python-magic>=0.4.27`: For magic number-based file detection
- `magika>=1.0.1`: Google's AI-powered file type detection
- `pytest>=8.4.2`: Testing framework
- `loguru>=0.7.3`: Logging (used in tests)

## Requirements

- Python >= 3.8

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest tests/ -v`
2. Code follows the existing style
3. New features include appropriate tests
4. Documentation is updated

## Acknowledgments

- [python-magic](https://github.com/ahupp/python-magic) for libmagic bindings
- [Google Magika](https://github.com/google/magika) for AI-powered file type detection
