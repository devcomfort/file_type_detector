# Choose an Inferencer

This guide helps you choose the right inferencer for your workload.

## Recommended Default

Start with `AutoInferencer(backend="hybrid")`.
It gives you one stable entry point and delegates to `HybridInferencer`, which uses Magic for all files and consults Magika when Magic returns text or an ambiguous type. Check the [backend conformance report](../reference/backend-conformance.md) against your target runtime rather than relying on one cross-platform percentage.

Content-based examples below assume that each supplied path is an existing file.

```python
from filetype_detector import AutoInferencer

inferencer = AutoInferencer(backend="hybrid")
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions  # True
ft.mime_types             # ('application/pdf',)
```

## Quick Decision Guide

| Goal | Best choice | Why |
|------|-------------|-----|
| Fastest possible detection | `LexicalInferencer` | Reads the extension from the path and does no file I/O |
| Reliable content-based detection | `MagicInferencer` | Uses libmagic and works well for binary formats |
| Highest precision for text files | `MagikaInferencer` | Uses a trained model and can return confidence scores |
| Good default for mixed workloads | `HybridInferencer` or `AutoInferencer(backend="hybrid")` | Balances speed and specificity |
| One public entry point | `AutoInferencer` | Keeps backend selection behind one interface |

## When to Use Each Inferencer

## `LexicalInferencer`

Use it when file extensions are already trustworthy and performance matters more than correction.

```python
from filetype_detector import LexicalInferencer

inferencer = LexicalInferencer()
ft = inferencer.infer("report.pdf")
'.pdf' in ft.extensions  # True

# No extension
inferencer.infer("makefile")  # Raises ValueError
```

## `MagicInferencer`

Use it when file content matters and you want a lightweight, rule-based detector.

```python
from filetype_detector import MagicInferencer

inferencer = MagicInferencer()
ft = inferencer.infer("file_without_ext")
ft.extensions  # e.g. ('.pdf',) based on content
ft.mime_types  # e.g. ('application/pdf',)
```

## `MagikaInferencer`

Use it when you need finer distinctions between text-based formats or confidence scores.

```python
from filetype_detector import MagikaInferencer

inferencer = MagikaInferencer()
ft = inferencer.infer("script.py")
'.py' in ft.extensions  # True

# Confidence score (returns str + float, not FileType)
extension, score = inferencer.infer_with_score("data.json")
```

## `HybridInferencer`

Use it when your workload mixes binary and text files and you want one strong default.

```python
from filetype_detector import HybridInferencer

inferencer = HybridInferencer()
ft = inferencer.infer("script.py")
'.py' in ft.extensions  # True
```

## Known Limitations

| Inferencer | Limitation |
|------------|------------|
| `Lexical` | Trusts a present extension; missing extensions raise `ValueError` |
| `Magic` | `text/plain` covers many text formats; `.py`, `.json`, `.csv` all look the same |
| `Magic` | Compound Document formats (`.doc`, `.ppt`, `.xls`) share a MIME type — multiple extension candidates returned |
| `Magika` | HWP not in training data — returns empty `FileType` |
| `Magika` | ZIP-based formats (HWPX, ODF, ePub) may be misclassified (e.g., HWPX → `.epub`) |
| `Magika` | Advantage over Magic is strongest for text files; binary accuracy is comparable |
| `Hybrid` | Magika activates only for `text/*` and other ambiguous MIME types; precise Magic results bypass it |

## Rule of Thumb

Use `lexical` for trust, `magic` for validation, `magika` for text precision, and `hybrid` for mixed real-world input.

See [Inference Strategies](../explanation/inference-strategies.md) if you want the design rationale behind these trade-offs.