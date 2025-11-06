# Frequently Asked Questions

Common questions and answers about `filetype-detector`.

## General Questions

### Which inferencer should I use?

See the [User Guide](user-guide.md) for a comprehensive inferencer selection guide.

### Can I use multiple inferencers together?

Yes! You can chain inferencers or use them sequentially. See [User Guide](user-guide.md#custom-inferencer-chain) for patterns.

### What if a file doesn't have an extension?

- **LexicalInferencer**: Returns empty string `''`
- **MagicInferencer**: Detects from content, returns extension
- **MagikaInferencer**: Detects from content, returns extension
- **CascadingInferencer**: Detects from content, returns extension

## Technical Questions

### Why does Magika return a list sometimes?

Magika's API returns extensions as a list (e.g., `['py', 'pyi']`). The inferencers automatically extract the first extension and format it with a leading dot.

### Can I get confidence scores?

Yes, but only with `MagikaInferencer` directly:

```python
from filetype_detector.magika_inferencer import MagikaInferencer

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

Yes, `MagicInferencer` and `CascadingInferencer` require the `libmagic` system library. See [Getting Started](getting-started.md#system-requirements) for installation instructions.

### Can I use it without Magika?

Yes! If you don't need AI-powered detection, you can use:
- `LexicalInferencer` (no dependencies)
- `MagicInferencer` (requires libmagic only)

## Usage Questions

### Can I use it with asyncio?

Not directly, but you can wrap it. See [User Guide](user-guide.md#examples) for async patterns.

### How do I process thousands of files?

See [User Guide](user-guide.md#performance) for batch processing strategies and optimization tips.

### Can I extend the inferencers?

Yes! See [Base Classes API](api/base.md#creating-custom-inferencers) for instructions on creating custom inferencers.

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

See the [User Guide](user-guide.md#best-practices) for best practices and optimization tips.

## Getting Help

1. Check the [User Guide](user-guide.md) for comprehensive usage instructions, examples, and performance tips
2. Check [API Documentation](api/base.md) for complete API reference
3. Open an issue on GitHub for bugs or feature requests

