# Base Classes

## BaseInferencer

Abstract base class for all file type inferencers.

```python
from filetype_detector import BaseInferencer
```

### Description

The `BaseInferencer` class provides a common interface for all inferencer implementations. It defines the abstract `infer` method that must be implemented by subclasses.

### Class Definition

```python
class BaseInferencer(ABC):
    """Abstract base class for file format inference."""
```

### Methods

#### `infer(file_path: Union[Path, str]) -> FileType`

Abstract method that must be implemented by all inferencer subclasses.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file whose format should be inferred. Can be a `Path` object or a string representing the file system path.

**Returns:**

- `FileType`: A frozen dataclass holding `extensions: tuple[str, ...]` and `mime_types: tuple[str, ...]`.

**Raises:**

- `NotImplementedError`: If the subclass does not implement this method.

**Example:**

```python
from filetype_detector import BaseInferencer, FileType
from typing import Union
from pathlib import Path

class CustomInferencer(BaseInferencer):
    def infer(self, file_path: Union[Path, str]) -> FileType:
        # Custom implementation
        return FileType.from_extension(".custom")
```

### Creating Custom Inferencers

To create a custom inferencer, subclass `BaseInferencer` and implement the `infer` method:

```python
from filetype_detector import BaseInferencer, FileType
from typing import Union
from pathlib import Path

class MyCustomInferencer(BaseInferencer):
    """Custom inferencer implementation."""
    
    def infer(self, file_path: Union[Path, str]) -> FileType:
        """Infer file type using custom logic."""
        path_obj = Path(file_path)
        
        if path_obj.exists():
            size = path_obj.stat().st_size
            if size == 0:
                return FileType.from_extension(".empty")
            elif size < 100:
                return FileType.from_extension(".small")
        
        return FileType(extensions=(), mime_types=())
```

### Best Practices

1. **Validate Input**: Always validate that the file exists and is accessible
2. **Handle Errors**: Raise appropriate exceptions (`FileNotFoundError`, `ValueError`, etc.)
3. **Return `FileType`**: Use `FileType.from_extension(ext)` or `FileType.from_mimetype(mime)` for correct MIME resolution
4. **Type Hints**: Use proper type hints for better IDE support
5. **Documentation**: Provide clear docstrings following numpy-style format

