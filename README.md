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

**Recommended**: Use `CascadingInferencer` for the best balance of performance and accuracy:

```python
from filetype_detector.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
```

For more examples and usage patterns, see the [User Guide](https://filetype-detector.readthedocs.io/user-guide/).

## Performance Comparison

Choose the right inferencer based on your needs:

| Inferencer | Avg. Time (per file) | Memory | Throughput | Best For |
|------------|---------------------|--------|------------|----------|
| **LexicalInferencer** | < 0.001ms | Minimal | 50,000+ files/sec | Trusted extensions |
| **MagicInferencer** | ~1-5ms | Low | 200-500 files/sec | Content-based detection |
| **MagikaInferencer** | ~5-10ms* | High** | 100-200 files/sec | Highest accuracy (text) |
| **CascadingInferencer** | ~1-6ms | Medium | 150-400 files/sec | **⭐ Recommended default** |

\* After initial model load (~100-200ms one-time overhead)  
\*\* Model loaded into memory (~50-100MB)

### Recommendation

**For most use cases**: Use `CascadingInferencer` - it automatically optimizes by using Magic for binary files and Magika for text files, providing the best balance of performance and accuracy.

**For specific needs**:
- **Maximum speed**: `LexicalInferencer` (when extensions are trusted)
- **Content-based detection**: `MagicInferencer` (general purpose, binary files)
- **Highest accuracy**: `MagikaInferencer` (text files, confidence scores)

## Available Inferencers

### LexicalInferencer

Fastest method - extracts file extensions directly from paths without reading file contents.

```python
from filetype_detector.lexical_inferencer import LexicalInferencer

inferencer = LexicalInferencer()
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
extension = inferencer.infer("file_without_ext")  # Returns: ''
```

### MagicInferencer

Uses `python-magic` (libmagic) to detect file types based on magic numbers and file signatures.

```python
from filetype_detector.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()
extension = inferencer.infer("file.dat")  # Returns actual type based on content
```

**System Requirements**: Requires `libmagic` system library. See [Installation](#installation) section.

### MagikaInferencer

AI-powered detection with confidence scores. Especially effective for text files.

```python
from filetype_detector.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()
extension = inferencer.infer("script.py")  # Returns: '.py'

# With confidence score
extension, score = inferencer.infer_with_score("data.json")  # Returns: ('.json', 0.98)
```

### CascadingInferencer ⭐ Recommended

Smart two-stage approach: uses Magic for all files, then Magika for text files.

```python
from filetype_detector.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()

# Text file - uses Magic then Magika
extension = inferencer.infer("script.py")  # Returns: '.py' (from Magika)

# Binary file - uses Magic only
extension = inferencer.infer("document.pdf")  # Returns: '.pdf' (from Magic)
```

**System Requirements**: Requires `libmagic` system library. See [Installation](#installation) section.

## Key Features

- ✅ **Multiple inference strategies** - Choose the right method for your use case
- ✅ **Type-safe API** - Full type hints and type-safe method selection
- ✅ **Flexible input** - Supports both `Path` objects and string paths
- ✅ **Performance optimized** - Cascading inferencer intelligently combines methods
- ✅ **Well-tested** - Comprehensive test suite
- ✅ **Extensible** - Base class architecture for custom implementations

For detailed usage examples, error handling, and advanced patterns, see the [User Guide](https://filetype-detector.readthedocs.io/user-guide/).

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

## Documentation

📚 **Full documentation available at**: [https://filetype-detector.readthedocs.io](https://filetype-detector.readthedocs.io)

- **[Getting Started](https://filetype-detector.readthedocs.io/getting-started/)** - Installation and basic usage
- **[User Guide](https://filetype-detector.readthedocs.io/user-guide/)** - Comprehensive guide with examples and performance tips
- **[API Reference](https://filetype-detector.readthedocs.io/api/base/)** - Complete API documentation

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
