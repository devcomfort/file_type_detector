# MagikaInferencer

AI-powered file type detection using Google's Magika model.

```python
from file_type_infer.magika_inferencer import MagikaInferencer
```

## Overview

The `MagikaInferencer` uses Google's Magika AI model for advanced file type detection. It excels at detecting specific text file types (Python, JavaScript, JSON, INI, etc.) and provides confidence scores for predictions.

## Class Definition

```python
class MagikaInferencer(BaseInferencer):
    """Magika inferencer that uses Google's Magika AI to infer file format."""
```

## Methods

### `infer(file_path: Union[Path, str]) -> str`

Public API that returns only the file extension.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file to analyze. Can be a string or `Path` object.

**Returns:**

- `str`: File extension with leading dot (e.g., `'.pdf'`, `'.txt'`). The exact format depends on Magika's output format.

**Raises:**

- `FileNotFoundError`: If the file does not exist.
- `ValueError`: If the path is not a file.
- `RuntimeError`: If Magika fails to analyze the file.

**Examples:**

```python
from file_type_infer.magika_inferencer import MagikaInferencer
from pathlib import Path

inferencer = MagikaInferencer()

# String path
extension = inferencer.infer('document.pdf')  # Returns: '.pdf'

# Path object
extension = inferencer.infer(Path('notes.txt'))  # Returns: '.txt'
```

### `infer_with_score(file_path: Union[Path, str], prediction_mode: PredictionMode = PredictionMode.MEDIUM_CONFIDENCE) -> Tuple[str, float]`

Core implementation that returns both extension and confidence score.

**Parameters:**

- `file_path` (`Union[Path, str]`): Path to the file to analyze. Can be a string or `Path` object.
- `prediction_mode` (`PredictionMode`, optional): Magika prediction mode controlling confidence level. Defaults to `PredictionMode.MEDIUM_CONFIDENCE`.

**Returns:**

- `Tuple[str, float]`: Tuple of `(extension, confidence_score)` where `extension` includes the leading dot (e.g., `'.pdf'`) and `confidence_score` is a float between 0.0 and 1.0.

**Raises:**

- `FileNotFoundError`: If the file does not exist.
- `ValueError`: If the path is not a file.
- `RuntimeError`: If Magika fails to analyze the file.

**Examples:**

```python
from file_type_infer.magika_inferencer import MagikaInferencer
from magika import PredictionMode

inferencer = MagikaInferencer()

# Default prediction mode
extension, score = inferencer.infer_with_score('document.pdf')
print(f"{extension}, {score:.2%}")  # Output: '.pdf, 99.00%'

# High confidence mode
extension, score = inferencer.infer_with_score(
    'script.py',
    prediction_mode=PredictionMode.HIGH_CONFIDENCE
)
```

## Prediction Modes

Magika supports different prediction modes:

- `PredictionMode.MEDIUM_CONFIDENCE` (default): Balanced speed and accuracy
- `PredictionMode.HIGH_CONFIDENCE`: Higher accuracy, slightly slower
- `PredictionMode.BEST_GUESS`: Fastest, lower threshold

```python
from magika import PredictionMode

inferencer = MagikaInferencer()

# Medium confidence (default)
ext, score = inferencer.infer_with_score(
    "file.py",
    prediction_mode=PredictionMode.MEDIUM_CONFIDENCE
)

# High confidence
ext, score = inferencer.infer_with_score(
    "file.py",
    prediction_mode=PredictionMode.HIGH_CONFIDENCE
)
```

## Usage Examples

### Basic Usage

```python
from file_type_infer.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()
extension = inferencer.infer("script.py")
print(extension)  # Output: '.py'
```

### With Confidence Scores

```python
inferencer = MagikaInferencer()
extension, confidence = inferencer.infer_with_score("data.json")
print(f"Type: {extension}, Confidence: {confidence:.2%}")
# Output: Type: .json, Confidence: 98.00%
```

### Detecting Specific Text File Types

```python
inferencer = MagikaInferencer()

# Python file
ext = inferencer.infer("script.py")  # Returns: '.py'

# JavaScript file
ext = inferencer.infer("code.js")    # Returns: '.js'

# JSON file (even with wrong extension)
ext = inferencer.infer("data.txt")   # May return: '.json'

# INI configuration
ext = inferencer.infer("config.ini") # Returns: '.ini'
```

### Filtering by Confidence

```python
inferencer = MagikaInferencer()

extension, score = inferencer.infer_with_score("file.py")

if score >= 0.95:
    print(f"High confidence: {extension}")
elif score >= 0.80:
    print(f"Medium confidence: {extension}")
else:
    print(f"Low confidence: {extension}")
```

### Error Handling

```python
from file_type_infer.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()

try:
    extension = inferencer.infer("nonexistent.pdf")
except FileNotFoundError:
    print("File not found")
except ValueError:
    print("Path is not a file")
except RuntimeError as e:
    print(f"Magika failed: {e}")
```

## How It Works

1. **File Validation**: Checks if file exists and is accessible
2. **AI Inference**: Uses Magika model to analyze file content
3. **Extension Extraction**: Extracts extension from Magika's output
4. **Format Normalization**: Ensures extension starts with dot

## Performance

- **Speed**: ~5-10ms per file (after model load)
- **Model Load**: ~100-200ms one-time overhead
- **Memory**: High (~50-100MB for model)
- **Throughput**: 100-200 files/second

## When to Use

✅ **Good for:**
- Highest accuracy requirements
- Text file type detection (especially effective)
- Need confidence scores
- Detecting specific code/data formats
- Files with misleading extensions

❌ **Not suitable for:**
- Maximum performance requirements (use LexicalInferencer)
- Binary-only workflows (use MagicInferencer)
- Very high-volume processing

## Model Loading

The Magika model is loaded when the inferencer is instantiated:

```python
# Model loads here (~100-200ms)
inferencer = MagikaInferencer()

# Subsequent calls are faster (~5-10ms)
extension = inferencer.infer("file.py")
```

**Best Practice**: Create one instance and reuse it for multiple files.

## Output Format

Magika returns extensions in different formats. The `MagikaInferencer` normalizes this:

- **List format**: `['py', 'pyi']` → Returns first: `.py`
- **String format**: `'json'` → Returns: `.json`
- **Empty result**: Falls back to Magic result (in CascadingInferencer)

## Comparison with Other Inferencers

| Aspect | MagikaInferencer | MagicInferencer | LexicalInferencer |
|--------|-----------------|-----------------|-------------------|
| Text file accuracy | Highest (~99%) | Medium | Low (extension only) |
| Binary file accuracy | High | High | Low (extension only) |
| Speed | Slower | Fast | Fastest |
| Confidence scores | Yes | No | No |
| Memory usage | High | Low | Minimal |

## Limitations

1. **Model size**: Requires ~50-100MB memory
2. **Load time**: Initial model load takes 100-200ms
3. **Performance**: Slower than Magic-based detection
4. **Return format**: May return list format (handled automatically)

