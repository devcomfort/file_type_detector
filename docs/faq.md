# Frequently Asked Questions

Quick answers and troubleshooting notes for `filetype-detector`.

## General Questions

### Which inferencer should I use?

See [Choose an Inferencer](how-to/choose-an-inferencer.md) for a task-based recommendation guide.

### How accurate is this library?

Across 598 tested file formats:

| Strategy | Accuracy |
|----------|:--------:|
| Lexical (extension only) | 19.4% |
| Magic (libmagic) | 59.9% |
| Magika (Google AI) | 62.5% |
| **Hybrid (Magic + Magika)** | **74.2%** |

See [Accuracy Benchmarks](reference/accuracy-benchmarks.md) for per-format data and methodology.

### Can I use multiple inferencers together?

Yes. You can chain inferencers or use them sequentially. See [Examples and Patterns](user-guide.md#custom-inferencer-chain) for a concrete fallback pattern.

### What if a file doesn't have an extension?

- **LexicalInferencer**: Raises `ValueError`
- **MagicInferencer**: Detects content and returns a `FileType`
- **MagikaInferencer**: Detects content and returns a `FileType`
- **HybridInferencer**: Detects content and returns a `FileType`

## Technical Questions

### Why does Magika return a list sometimes?

Magika can report multiple extensions. `MagikaInferencer.infer()` normalizes all of them into `FileType.extensions`; `infer_with_score()` returns the first extension with its confidence score.

### Can I get confidence scores?

Yes, but only with `MagikaInferencer` directly:

```python
from filetype_detector import MagikaInferencer

inferencer = MagikaInferencer()
extension, score = inferencer.infer_with_score("file.py")
```

Note: `AutoInferencer(backend="magika")` doesn't support scores.

### What happens if detection fails?

It depends on the inferencer:
- **LexicalInferencer**: Raises `ValueError` when the path has no extension
- **MagicInferencer**: Raises `RuntimeError` if MIME type cannot be determined
- **MagikaInferencer**: Raises `RuntimeError` if Magika fails
- **HybridInferencer**: Falls back to Magic result if Magika fails

## Installation Questions

### Do I need system libraries?

Yes, `MagicInferencer` and `HybridInferencer` require the `libmagic` system library. See [Getting Started](getting-started.md#system-requirements) for installation instructions.

### Can I avoid loading the Magika model?

Yes. Select a backend that does not invoke Magika:
- `LexicalInferencer` (no file I/O)
- `MagicInferencer` (requires the `libmagic` system library)

Magika remains an installation dependency in the current package metadata.

## Usage Questions

### Can I use it with asyncio?

Not directly, but you can wrap it. See [Examples and Patterns](user-guide.md#examples) for async patterns.

### How do I process thousands of files?

See [Examples and Patterns](user-guide.md#performance) for batch processing strategies and optimization tips.

### Can I extend the inferencers?

Yes! See [BaseInferencer API](api/base_inferencer.md#creating-custom-inferencers) for instructions on creating custom inferencers.

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
- Consider `HybridInferencer` for mixed content

### Low confidence scores

- Use `PredictionMode.HIGH_CONFIDENCE`
- File content might be ambiguous
- Consider validation or manual review

## Best Practices

See [Examples and Patterns](user-guide.md#best-practices) for best practices and optimization tips.

## Getting Help

1. Check [Examples and Patterns](user-guide.md) for usage instructions, examples, and performance tips
2. Check [API Documentation](api/base_inferencer.md) for complete API reference
3. Open an issue on GitHub for bugs or feature requests

