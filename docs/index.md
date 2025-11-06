# filetype-detector

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
from filetype_detector.mixture_inferencer import CascadingInferencer

# Recommended: Use CascadingInferencer for best balance
inferencer = CascadingInferencer()
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
```

## Installation

```bash
pip install filetype-detector
```

See [Getting Started](getting-started.md) for detailed installation instructions including system dependencies.

## Documentation

- **[Getting Started](getting-started.md)** - Installation and basic usage
- **[User Guide](user-guide.md)** - Comprehensive usage guide with examples and performance tips
- **[API Reference](api/base.md)** - Complete API documentation

## Requirements

- Python >= 3.8
- python-magic >= 0.4.27 (for MagicInferencer and CascadingInferencer)
- magika >= 1.0.1 (for MagikaInferencer and CascadingInferencer)

See [Getting Started](getting-started.md#system-requirements) for system library installation instructions.

## License

This project is open source.
