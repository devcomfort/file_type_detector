# Architecture

Understanding the internal architecture and design decisions of `filetype-detector`.

## Overview

`filetype-detector` follows an object-oriented design based on the Strategy pattern, where different inference algorithms are encapsulated as separate classes implementing a common interface.

## Core Components

### BaseInferencer (Abstract Base Class)

All inferencers inherit from `BaseInferencer`, which defines the common interface:

```python
class BaseInferencer(ABC):
    @abstractmethod
    def infer(self, file_path: Union[Path, str]) -> str:
        """Infer file format from path."""
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
4. **CascadingInferencer**: Hybrid two-stage approach

## Design Patterns

### Strategy Pattern

The library implements the Strategy pattern, allowing clients to choose inference algorithms dynamically:

```python
# Strategy selection
strategy = FILE_FORMAT_INFERENCER_MAP[method]
result = strategy(file_path)
```

### Template Method Pattern

`CascadingInferencer` uses a template method approach:
1. Common validation (file existence)
2. Algorithm-specific detection
3. Result formatting

## Module Structure

```
filetype_detector/
├── __init__.py
├── base_inferencer.py      # Abstract base class
├── lexical_inferencer.py   # Path-based inference
├── magic_inferencer.py     # libmagic-based inference
├── magika_inferencer.py    # AI-powered inference
├── mixture_inferencer.py   # Cascading inference
└── inferencer.py           # Type definitions and map
```

## Data Flow

### LexicalInferencer

```
File Path → Path.suffix → Lowercase → Extension
```

### MagicInferencer

```
File Path → Validation → magic.from_file() → MIME Type → 
mimetypes.guess_extension() → Extension
```

### MagikaInferencer

```
File Path → Validation → Magika.identify_path() → 
result.output.extensions → Format → Extension
```

### CascadingInferencer

```
File Path → Validation → Magic Detection → 
Is text/*? → Yes: Magika Detection → Extension
            No: Magic Result → Extension
```

## Extension Points

### Adding Custom Inferencers

To add a custom inferencer:

1. **Subclass BaseInferencer**:
```python
from filetype_detector.base_inferencer import BaseInferencer

class CustomInferencer(BaseInferencer):
    def infer(self, file_path: Union[Path, str]) -> str:
        # Your logic here
        return ".custom"
```

2. **Add to Map** (optional):
```python
from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP

FILE_FORMAT_INFERENCER_MAP["custom"] = lambda path: CustomInferencer().infer(path)
```

## Error Handling Strategy

All inferencers follow a consistent error handling pattern:

1. **FileNotFoundError**: File doesn't exist
2. **ValueError**: Path is not a file (e.g., is a directory)
3. **RuntimeError**: Detection logic failure

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
InferencerType = Union[Literal["magika", "magic"], None]
```

This ensures:
- Only valid methods can be used
- IDE autocompletion works
- Type checkers catch errors

### Return Types

All inferencers return `str` (extension with dot prefix) for consistency, except `MagikaInferencer.infer_with_score()` which returns `Tuple[str, float]`.

## Performance Considerations

### Lazy Evaluation

- Magika model loads only when `MagikaInferencer` is instantiated
- No pre-loading of models or libraries

### Instance Reuse

All inferencers are designed to be reused:

```python
# Good - reuse instance
inferencer = MagicInferencer()
for file in files:
    extension = inferencer.infer(file)

# Bad - creates new instance each time
for file in files:
    inferencer = MagicInferencer()  # Don't do this
    extension = inferencer.infer(file)
```

### Cascading Optimization

`CascadingInferencer` optimizes by:
- Only loading Magika model once
- Skipping Magika for binary files
- Caching Magic results per file

## Testing Architecture

The test suite follows a fixture-based approach:

```
tests/
├── conftest.py              # Shared fixtures
├── test_lexical_inferencer.py
├── test_magic_inferencer.py
├── test_magika_inferencer.py
└── test_cascading_inferencer.py
```

**Key Testing Patterns:**
- Fixtures for sample files
- Mocking for unit tests
- Real files for integration tests
- Loguru for test logging

## Future Extensibility

The architecture supports future enhancements:

1. **New Inferencers**: Easy to add via `BaseInferencer`
2. **New Strategies**: Can add to `FILE_FORMAT_INFERENCER_MAP`
3. **Configuration**: Type system supports config-based selection
4. **Caching**: Can add caching layer without changing interfaces

## Design Principles

1. **Single Responsibility**: Each inferencer has one clear purpose
2. **Open/Closed**: Open for extension (new inferencers), closed for modification
3. **Dependency Inversion**: Depend on abstractions (`BaseInferencer`)
4. **Interface Segregation**: Minimal, focused interface
5. **DRY**: Common logic in base class or utilities

