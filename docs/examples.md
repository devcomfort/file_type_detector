# Examples

Real-world examples demonstrating how to use `file-type-infer` effectively.

## Basic Examples

### Simple File Type Detection

```python
from file_type_infer.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()
extension = inferencer.infer("document.pdf")
print(f"File type: {extension}")  # Output: File type: .pdf
```

### Detecting Files Without Extensions

```python
from file_type_infer.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()

# File without extension
extension = inferencer.infer("file_without_ext")
print(f"Detected type: {extension}")  # Output: Detected type: .txt
```

### Detecting Wrong Extensions

```python
from file_type_infer.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()

# File named .txt but contains JSON
extension, confidence = inferencer.infer_with_score("data.txt")
print(f"Actual type: {extension}, Confidence: {confidence:.2%}")
# Output: Actual type: .json, Confidence: 95.00%
```

## Advanced Examples

### Batch Processing with Error Handling

```python
from file_type_infer.mixture_inferencer import CascadingInferencer
from pathlib import Path
from typing import Dict

def batch_detect(file_paths: list[Path]) -> Dict[str, str]:
    """Detect file types for multiple files."""
    inferencer = CascadingInferencer()
    results = {}
    
    for file_path in file_paths:
        try:
            extension = inferencer.infer(file_path)
            results[str(file_path)] = extension
        except FileNotFoundError:
            results[str(file_path)] = "ERROR: File not found"
        except ValueError:
            results[str(file_path)] = "ERROR: Not a file"
        except RuntimeError as e:
            results[str(file_path)] = f"ERROR: {e}"
    
    return results

# Usage
files = [Path("doc1.pdf"), Path("script.py"), Path("data.json")]
results = batch_detect(files)
for file, ext in results.items():
    print(f"{file}: {ext}")
```

### File Type Validator

```python
from file_type_infer.magic_inferencer import MagicInferencer
from pathlib import Path

def validate_file_type(file_path: Path, expected_extension: str) -> bool:
    """Validate that file matches expected type."""
    inferencer = MagicInferencer()
    try:
        detected = inferencer.infer(file_path)
        return detected == expected_extension
    except Exception:
        return False

# Usage
is_pdf = validate_file_type(Path("document.pdf"), ".pdf")
print(f"Is PDF: {is_pdf}")  # Output: Is PDF: True
```

### Confidence-Based Filtering

```python
from file_type_infer.magika_inferencer import MagikaInferencer
from magika import PredictionMode
from pathlib import Path

def filter_by_confidence(
    file_path: Path, 
    min_confidence: float = 0.9
) -> tuple[str, float] | None:
    """Get file type only if confidence meets threshold."""
    inferencer = MagikaInferencer()
    extension, score = inferencer.infer_with_score(
        file_path, 
        prediction_mode=PredictionMode.HIGH_CONFIDENCE
    )
    
    if score >= min_confidence:
        return (extension, score)
    return None

# Usage
result = filter_by_confidence(Path("script.py"), min_confidence=0.9)
if result:
    ext, conf = result
    print(f"High confidence: {ext} ({conf:.2%})")
```

### Directory Scanner

```python
from file_type_infer.mixture_inferencer import CascadingInferencer
from pathlib import Path
from collections import Counter

def scan_directory(directory: Path) -> dict[str, int]:
    """Scan directory and count file types."""
    inferencer = CascadingInferencer()
    type_counts = Counter()
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                extension = inferencer.infer(file_path)
                type_counts[extension] += 1
            except Exception:
                type_counts["unknown"] += 1
    
    return dict(type_counts)

# Usage
stats = scan_directory(Path("./documents"))
for ext, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"{ext}: {count} files")
```

### Custom Inferencer Chain

```python
from file_type_infer.lexical_inferencer import LexicalInferencer
from file_type_infer.magic_inferencer import MagicInferencer
from pathlib import Path

def infer_with_fallback(file_path: Path) -> str:
    """Try lexical first, fallback to magic."""
    lexical = LexicalInferencer()
    extension = lexical.infer(file_path)
    
    # If no extension found, use magic
    if not extension:
        magic = MagicInferencer()
        extension = magic.infer(file_path)
    
    return extension

# Usage
result = infer_with_fallback(Path("file_without_ext"))
print(f"Detected: {result}")
```

### Type-Safe File Router

```python
from file_type_infer.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP
from pathlib import Path
from typing import Callable

class FileRouter:
    """Route files based on type."""
    
    def __init__(self, method: InferencerType = "magic"):
        self.inferencer = FILE_FORMAT_INFERENCER_MAP[method]
        self.handlers: dict[str, Callable] = {}
    
    def register(self, extension: str, handler: Callable):
        """Register a handler for an extension."""
        self.handlers[extension] = handler
    
    def route(self, file_path: Path):
        """Route file to appropriate handler."""
        extension = self.inferencer(file_path)
        handler = self.handlers.get(extension)
        
        if handler:
            return handler(file_path)
        return None

# Usage
router = FileRouter(method="magic")
router.register(".pdf", lambda p: print(f"Processing PDF: {p}"))
router.register(".py", lambda p: print(f"Processing Python: {p}"))

router.route(Path("document.pdf"))  # Output: Processing PDF: document.pdf
router.route(Path("script.py"))     # Output: Processing Python: script.py
```

### Using CascadingInferencer for Mixed Content

```python
from file_type_infer.mixture_inferencer import CascadingInferencer
from pathlib import Path

def process_mixed_files(file_paths: list[Path]):
    """Process files using cascading inference."""
    inferencer = CascadingInferencer()
    
    for file_path in file_paths:
        try:
            extension = inferencer.infer(file_path)
            
            if extension == ".pdf":
                print(f"{file_path}: Binary document")
            elif extension in [".py", ".js", ".json"]:
                print(f"{file_path}: Text-based code/data file")
            else:
                print(f"{file_path}: {extension}")
                
        except Exception as e:
            print(f"{file_path}: Error - {e}")

# Usage
files = [
    Path("document.pdf"),   # Binary - uses Magic only
    Path("script.py"),      # Text - uses Magic + Magika
    Path("data.json"),      # Text - uses Magic + Magika
]
process_mixed_files(files)
```

## Integration Examples

### With Pandas

```python
import pandas as pd
from file_type_infer.mixture_inferencer import CascadingInferencer
from pathlib import Path

def create_file_type_dataframe(directory: Path) -> pd.DataFrame:
    """Create DataFrame with file type information."""
    inferencer = CascadingInferencer()
    data = []
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                extension = inferencer.infer(file_path)
                data.append({
                    "file": file_path.name,
                    "path": str(file_path),
                    "extension": extension,
                    "size": file_path.stat().st_size
                })
            except Exception:
                pass
    
    return pd.DataFrame(data)

# Usage
df = create_file_type_dataframe(Path("./documents"))
print(df.groupby("extension").size())
```

### With FastAPI

```python
from fastapi import FastAPI, HTTPException
from file_type_infer.mixture_inferencer import CascadingInferencer
from pathlib import Path

app = FastAPI()
inferencer = CascadingInferencer()

@app.post("/detect/{file_path:path}")
async def detect_file_type(file_path: str):
    """API endpoint for file type detection."""
    try:
        extension = inferencer.infer(file_path)
        return {"file": file_path, "extension": extension}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

