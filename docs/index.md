# file-type-infer

A Python library for detecting file types using multiple inference strategies, including path-based extraction, magic number detection, and AI-powered content analysis.

## Features

- **Multiple Inference Methods**: Choose from lexical, magic-based, AI-powered, or cascading inference strategies
- **Type-Safe API**: Type hints and type-safe inference method selection  
- **Flexible Input**: Supports both `Path` objects and string paths
- **Performance Optimized**: Cascading inferencer intelligently combines methods for optimal performance
- **Well-Tested**: Comprehensive test suite with logging support
- **Extensible**: Base class architecture for custom inferencer implementations

## Quick Start

```python
from file_type_infer.inferencer import FILE_FORMAT_INFERENCER_MAP

# Get an inferencer
inferencer = FILE_FORMAT_INFERENCER_MAP["magic"]

# Infer file type
extension = inferencer("document.pdf")  # Returns: '.pdf'
```

## Installation

```bash
pip install file-type-infer
```

Or using rye:

```bash
rye sync
```

## Available Inferencers

### LexicalInferencer

Fastest method - extracts file extensions directly from paths.

```python
from file_type_infer.lexical_inferencer import LexicalInferencer

inferencer = LexicalInferencer()
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
```

### MagicInferencer

Uses libmagic for content-based file type detection.

```python
from file_type_infer.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()
extension = inferencer.infer("file_without_ext")  # Detects from content
```

### MagikaInferencer

AI-powered detection with confidence scores.

```python
from file_type_infer.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()
extension = inferencer.infer("script.py")  # Returns: '.py'
extension, score = inferencer.infer_with_score("data.json")  # With confidence
```

### CascadingInferencer

Smart two-stage approach - combines Magic and Magika for optimal performance.

```python
from file_type_infer.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()
extension = inferencer.infer("script.py")  # Uses Magic then Magika
```

## Documentation

- **[Getting Started](getting-started.md)** - Installation and quick examples
- **[User Guide](user-guide.md)** - Detailed usage instructions
- **[API Reference](api/base.md)** - Complete API documentation
- **[Examples](examples.md)** - Real-world usage examples
- **[Performance](performance.md)** - Performance considerations

## Requirements

- Python >= 3.8
- python-magic >= 0.4.27
- magika >= 1.0.1

## License

This project is open source.
