# Choose an Inferencer

This guide helps you choose the right inferencer for your workload.

## Recommended Default

Start with `UnifiedInferencer(backend="hybrid")`.
It gives you one stable entry point and delegates to `HybridInferencer`, which uses Magic for all files and consults Magika when Magic returns text or an ambiguous type. Check the [backend conformance report](../reference/backend-conformance.md) against your target runtime rather than relying on one cross-platform percentage.

Content-based examples below assume that each supplied path is an existing file.

```python
from filetype_detector import UnifiedInferencer

inferencer = UnifiedInferencer(backend="hybrid")
ft = inferencer.detect("document.pdf")
'.pdf' in ft.extensions  # True
ft.mime_types             # ('application/pdf',)
```

## Quick Decision Guide

| Goal | Best choice | Why |
|------|-------------|-----|
| Fastest possible detection | `LexicalInferencer` | Reads the extension from the path and does no file I/O |
| Reliable content-based detection | `MagicInferencer` | Uses libmagic and works well for binary formats |
| Highest precision for text files | `MagikaInferencer` | Uses a trained model and can return confidence scores |
| Good default for mixed workloads | `HybridInferencer` or `UnifiedInferencer(backend="hybrid")` | Balances speed and specificity |
| Identical labels across OSes | `TikaInferencer` or `UnifiedInferencer(backend="tika")` | A pinned Tika build does not read the OS MIME database |
| One public entry point | `UnifiedInferencer` | Keeps backend selection behind one interface |

## When to Use Each Inferencer

## `LexicalInferencer`

Use it when file extensions are already trustworthy and performance matters more than correction.

```python
from filetype_detector import LexicalInferencer

inferencer = LexicalInferencer()
ft = inferencer.detect("report.pdf")
'.pdf' in ft.extensions  # True

# No extension
inferencer.detect("makefile")  # Raises ValueError
```

## `MagicInferencer`

Use it when file content matters and you want a lightweight, rule-based detector.

```python
from filetype_detector import MagicInferencer

inferencer = MagicInferencer()
ft = inferencer.detect("file_without_ext")
ft.extensions  # e.g. ('.pdf',) based on content
ft.mime_types  # e.g. ('application/pdf',)
```

## `MagikaInferencer`

Use it when you need finer distinctions between text-based formats or confidence scores.

```python
from filetype_detector import MagikaInferencer

inferencer = MagikaInferencer()
ft = inferencer.detect("script.py")
'.py' in ft.extensions  # True

# Confidence score (returns str + float, not FileType)
extension, score = inferencer.detect_with_score("data.json")
```

## `HybridInferencer`

Use it when your workload mixes binary and text files and you want one strong default.

```python
from filetype_detector import HybridInferencer

inferencer = HybridInferencer()
ft = inferencer.detect("script.py")
'.py' in ft.extensions  # True
```

## `TikaInferencer`

Use it when results must be identical on Linux, macOS, and Windows. A pinned
Tika build returns its own MIME and extension labels instead of reading the
OS MIME database. Requires Java 11+ and the pinned JAR.

```python
from filetype_detector import TikaInferencer

TikaInferencer.download_jar()  # one-time; SHA-512 verified
inferencer = TikaInferencer()
ft = inferencer.detect("file_without_ext")
```

| Inferencer | Limitation |
|------------|------------|
| `Lexical` | Trusts a present extension; missing extensions raise `ValueError` |
| `Magic` | `text/plain` covers many text formats; `.py`, `.json`, `.csv` all look the same |
| `Magic` | Compound Document formats (`.doc`, `.ppt`, `.xls`) share a MIME type — multiple extension candidates returned |
| `Magika` | HWP not in training data — returns empty `FileType` |
| `Magika` | ZIP-based formats (HWPX, ODF, ePub) may be misclassified (e.g., HWPX → `.epub`) |
| `Magika` | Advantage over Magic is strongest for text files; binary accuracy is comparable |
| `Hybrid` | Magika activates only for `text/*` and other ambiguous MIME types; precise Magic results bypass it |
| `Tika` | Requires Java 11+ and the verified pinned JAR; first `detect()` pays the one-time JVM startup |

## Rule of Thumb

Use `lexical` for trust, `magic` for validation, `magika` for text precision, `tika` for cross-OS stability, and `hybrid` for mixed real-world input.

See [Inference Strategies](../explanation/inference-strategies.md) if you want the design rationale behind these trade-offs.