# Architecture

This page explains the internal structure of `filetype-detector` and the design decisions behind it.

## Overview

`filetype-detector` follows an object-oriented design based on the Strategy pattern, where different inference algorithms are encapsulated as separate classes implementing a common interface.

## Core Components

### BaseInferencer (Abstract Base Class)

All inferencers inherit from `BaseInferencer`, which defines the common interface:

```python
class BaseInferencer(ABC):
    @abstractmethod
    def infer(self, file_path: Union[Path, str]) -> FileType:
        """Infer a file type and return extensions with MIME types."""
        raise NotImplementedError
```

**Design Benefits:**
- Ensures consistent interface across all inferencers
- Enables polymorphic usage
- Makes it easy to add new inferencer types

### Concrete Implementations

1. **LexicalInferencer**: Path-based extraction
2. **MagicInferencer**: Content-based using libmagic
3. **MagikaInferencer**: AI-powered detection
4. **HybridInferencer**: Hybrid two-stage approach

## Design Patterns

### Strategy Pattern

The library implements the Strategy pattern, allowing clients to choose inference algorithms dynamically:

```python
# Strategy selection
strategy = AutoInferencer(backend=backend)
result = strategy.infer(file_path)
```

### Template Method Pattern

`HybridInferencer` uses a template method approach:
1. Common validation (file existence)
2. Algorithm-specific detection
3. Result formatting

## Module Structure

```
filetype_detector/
├── __init__.py
├── __main__.py             # Lazy launcher for the terminal UI
├── auto_inferencer.py      # Unified backend selector
├── demo.py                 # Textual file browser and strategy comparison
├── core/
│   ├── base_inferencer.py  # Abstract interface and path validation
│   └── file_type.py        # Immutable result type
└── strategies/
    ├── lexical_inferencer.py
    ├── magic_inferencer.py
    ├── magika_inferencer.py
    └── hybrid_inferencer.py
```

`__main__.py` imports the Textual interface only after validating CLI
arguments, keeping `--help` and argument errors fast.

## Data Flow

### LexicalInferencer

```
File Path → Path.suffix → Lowercase → FileType
```

### MagicInferencer

```
File Path → Validation → magic.from_file() → MIME Type →
FileType.from_mimetype()
```

### MagikaInferencer

```
File Path → Validation → Magika.identify_path() →
Extensions + MIME Type → FileType
```

### HybridInferencer

```
File Path → Validation → Magic Detection →
Is text/* or ambiguous MIME? → Yes: Magika Detection → FileType
                               No: Magic Result → FileType
```

The two-stage design keeps Magic's result unless text or an ambiguous MIME opens the Magika refinement path. The [backend conformance report](reference/backend-conformance.md) records this behavior separately for each supported runtime.

## Extension Points

### Adding Custom Inferencers

To add a custom inferencer:

1. **Subclass BaseInferencer**:
```python
from filetype_detector import BaseInferencer, FileType

class CustomInferencer(BaseInferencer):
    def infer(self, file_path: Union[Path, str]) -> FileType:
        # Build the shared result type so every strategy has the same contract.
        return FileType.from_extension(".custom")
```

2. **Register in `AutoInferencer`** (optional):
```python
from .my_inferencer import CustomInferencer

BackendType = Literal["lexical", "magic", "magika", "hybrid", "custom"]
_BACKEND_MAP["custom"] = CustomInferencer
```

## Error Handling Strategy

Content-based inferencers use the shared path validator. `LexicalInferencer`
does not access the filesystem; it raises `ValueError` when the supplied path
has no extension.

1. **FileNotFoundError**: A content-based inferencer cannot find the file
2. **ValueError**: The path is not a file, or a lexical path has no extension
3. **RuntimeError**: Detection logic fails

```python
# Common pattern across inferencers
if not path_obj.exists():
    raise FileNotFoundError(...)
if not path_obj.is_file():
    raise ValueError(...)
# Detection logic
if detection_fails:
    raise RuntimeError(...)
```

## Type System

### Type Safety

The library uses Python's type system for safety:

```python
BackendType = Literal["lexical", "magic", "magika", "hybrid"]
```

This ensures:
- Only valid methods can be used
- IDE autocompletion works
- Type checkers catch errors

### Return Types

All `infer()` implementations return `FileType`, which carries `extensions`
and `mime_types` tuples. `MagikaInferencer.infer_with_score()` is the one
specialized helper that returns `tuple[str, float]`.

## Performance Considerations

### Lazy Evaluation

- Magika models load on the first inference that needs them
- Binary-only `HybridInferencer` workloads never load Magika

### Instance Reuse

All inferencers are designed to be reused:

```python
# Good - reuse instance
inferencer = MagicInferencer()
for file in files:
    file_type = inferencer.infer(file)

# Bad - creates new instance each time
for file in files:
    inferencer = MagicInferencer()  # Don't do this
    file_type = inferencer.infer(file)
```

### Hybrid Optimization

`HybridInferencer` optimizes by:
- Loading one Magika model lazily per inferencer instance
- Skipping Magika for MIME types that Magic identifies precisely
- Falling back to Magic when Magika fails or has low confidence

## Testing Architecture

The test suite follows a fixture-based approach:

```
tests/
├── conftest.py              # Shared fixtures
├── test_lexical_inferencer.py
├── test_magic_inferencer.py
├── test_magika_inferencer.py
└── test_hybrid_inferencer.py
```

**Key Testing Patterns:**
- Canonical fixture files for format coverage
- Temporary files for input and error boundaries
- Behavior-focused assertions against public results

## Future Extensibility

The architecture supports future enhancements:

1. **New Inferencers**: Easy to add via `BaseInferencer`
2. **New Strategies**: Can add new backends to `AutoInferencer`
3. **Configuration**: Type system supports config-based selection
4. **Caching**: Can add caching layer without changing interfaces

## Design Principles

1. **Single Responsibility**: Each inferencer has one clear purpose
2. **Open/Closed**: Open for extension (new inferencers), closed for modification
3. **Dependency Inversion**: Depend on abstractions (`BaseInferencer`)
4. **Interface Segregation**: Minimal, focused interface
5. **DRY**: Common logic in base class or utilities

