# Frequently Asked Questions

Common questions and answers about `file-type-infer`.

## General Questions

### Which inferencer should I use?

**For most use cases**: Use `CascadingInferencer` - it provides the best balance of performance and accuracy.

**For specific needs**:
- **Maximum speed**: `LexicalInferencer` (trusted extensions only)
- **Content-based detection**: `MagicInferencer` (general purpose)
- **Highest accuracy (text files)**: `MagikaInferencer` (with confidence scores)

### Can I use multiple inferencers together?

Yes! You can chain inferencers or use them sequentially:

```python
from file_type_infer.lexical_inferencer import LexicalInferencer
from file_type_infer.magic_inferencer import MagicInferencer

lexical = LexicalInferencer()
magic = MagicInferencer()

def detect_with_fallback(file_path):
    ext = lexical.infer(file_path)
    if not ext:
        ext = magic.infer(file_path)
    return ext
```

### What if a file doesn't have an extension?

- **LexicalInferencer**: Returns empty string `''`
- **MagicInferencer**: Detects from content, returns extension
- **MagikaInferencer**: Detects from content, returns extension
- **CascadingInferencer**: Detects from content, returns extension

## Performance Questions

### How fast is each inferencer?

Approximate speeds (per file):
- LexicalInferencer: < 0.001ms (fastest)
- MagicInferencer: ~1-5ms (fast)
- MagikaInferencer: ~5-10ms (slower, but accurate)
- CascadingInferencer: ~1-6ms (balanced)

### Can I cache results?

Yes! You can implement caching:

```python
from functools import lru_cache
from file_type_infer.magic_inferencer import MagicInferencer

class CachedMagicInferencer(MagicInferencer):
    @lru_cache(maxsize=1000)
    def infer(self, file_path):
        return super().infer(str(file_path))
```

### How much memory does Magika use?

The Magika model uses approximately 50-100MB of memory when loaded. It's loaded once when `MagikaInferencer` is instantiated and stays in memory while the instance exists.

## Accuracy Questions

### How accurate is each method?

- **LexicalInferencer**: Low accuracy (only reads extension)
- **MagicInferencer**: High accuracy (content-based, ~95%+)
- **MagikaInferencer**: Highest accuracy (AI-powered, ~99% for text files)
- **CascadingInferencer**: High accuracy (combines both)

### Which is best for text files?

`MagikaInferencer` or `CascadingInferencer` - Magika excels at detecting specific text file types (Python, JavaScript, JSON, etc.).

### Which is best for binary files?

`MagicInferencer` or `CascadingInferencer` - both use Magic which is reliable for binary files.

## Technical Questions

### Why does Magika return a list sometimes?

Magika's API returns extensions as a list (e.g., `['py', 'pyi']`). The inferencers automatically extract the first extension and format it with a leading dot.

### Can I get confidence scores?

Yes, but only with `MagikaInferencer` directly:

```python
from file_type_infer.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()
extension, score = inferencer.infer_with_score("file.py")
```

Note: `FILE_FORMAT_INFERENCER_MAP["magika"]` doesn't support scores.

### What happens if detection fails?

It depends on the inferencer:
- **LexicalInferencer**: Returns empty string for no extension
- **MagicInferencer**: Raises `RuntimeError` if MIME type cannot be determined
- **MagikaInferencer**: Raises `RuntimeError` if Magika fails
- **CascadingInferencer**: Falls back to Magic result if Magika fails

## Installation Questions

### Do I need system libraries?

Yes, `MagicInferencer` and `CascadingInferencer` require the `libmagic` system library.

**Installation by OS:**

- **Ubuntu/Debian**: `sudo apt-get install libmagic1`
- **Fedora/RHEL/CentOS**: `sudo dnf install file-libs` (or `sudo yum install file-libs`)
- **Arch Linux**: `sudo pacman -S file`
- **macOS**: `brew install libmagic` or `sudo port install file`
- **Windows**: `pip install python-magic-bin` (requires special package)
- **Alpine Linux**: `apk add --no-cache file`

### How do I verify libmagic is installed?

Run:
```bash
file --version
```

If it prints a version number (e.g., `file-5.x`), `libmagic` is installed correctly.

### Can I use it without Magika?

Yes! If you don't need AI-powered detection, you can use:
- `LexicalInferencer` (no dependencies)
- `MagicInferencer` (requires libmagic)
- `CascadingInferencer` (requires both, but Magic-only for binaries)

## Usage Questions

### Can I use it with asyncio?

Not directly, but you can wrap it:

```python
import asyncio
from file_type_infer.magic_inferencer import MagicInferencer

async def async_detect(file_path):
    loop = asyncio.get_event_loop()
    inferencer = MagicInferencer()
    return await loop.run_in_executor(None, inferencer.infer, file_path)
```

### How do I process thousands of files?

Use batch processing with instance reuse:

```python
from file_type_infer.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()  # Create once

for file_path in thousands_of_files:
    extension = inferencer.infer(file_path)
    # Process result
```

### Can I extend the inferencers?

Yes! Subclass `BaseInferencer`:

```python
from file_type_infer.base_inferencer import BaseInferencer

class CustomInferencer(BaseInferencer):
    def infer(self, file_path):
        # Your logic
        return ".custom"
```

## Troubleshooting

### "File not found" error

Make sure:
1. File path is correct
2. File exists
3. You have read permissions

### "Cannot determine MIME type" error

- File might be corrupted
- File might be empty
- System libmagic might not recognize the format

### Magika is slow

- Model loads once (~100-200ms)
- Subsequent calls are faster (~5-10ms)
- Reuse inferencer instance
- Consider `CascadingInferencer` for mixed content

### Low confidence scores

- Use `PredictionMode.HIGH_CONFIDENCE`
- File content might be ambiguous
- Consider validation or manual review

## Best Practices

### Do
- ✅ Reuse inferencer instances
- ✅ Handle exceptions properly
- ✅ Use `CascadingInferencer` for general use
- ✅ Cache results for repeated files
- ✅ Use type hints for better IDE support

### Don't
- ❌ Create new inferencer instances in loops
- ❌ Ignore exceptions
- ❌ Use Magika for high-volume binary-only workflows
- ❌ Assume extensions are always correct
- ❌ Forget to install system dependencies

## Getting Help

1. Check the [User Guide](user-guide.md)
2. Review [Examples](examples.md)
3. Check [API Documentation](api/base.md)
4. Open an issue on GitHub

