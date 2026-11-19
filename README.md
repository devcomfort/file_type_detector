# filetype-detector

[![CI](https://github.com/devcomfort/file_type_detector/actions/workflows/ci.yml/badge.svg)](https://github.com/devcomfort/file_type_detector/actions/workflows/ci.yml)
[![Backend conformance](https://github.com/devcomfort/file_type_detector/actions/workflows/backend-conformance.yml/badge.svg)](https://github.com/devcomfort/file_type_detector/actions/workflows/backend-conformance.yml)

A Python library for detecting file types using multiple inference strategies, including path-based extraction, magic number detection, AI-powered content analysis, and pinned Apache Tika detection.

## Backend Conformance

Backend behavior is checked against independently reviewed MIME and extension
facts on Linux, macOS, and Windows. The report preserves raw detector output,
normalized semantic output, runtime versions, correctness, and cross-platform
divergence. It does not reduce runtime-dependent behavior to one static
percentage.

See [Backend Conformance](docs/reference/backend-conformance.md) for the
methodology, latest workflow artifact, and reproduction commands.

## Features

- **Multiple Inference Methods**: Choose from lexical, magic-based, AI-powered, Apache Tika, or hybrid inference strategies
- **OS-Independent Labels**: `TikaInferencer` returns identical MIME and extension labels on Linux, macOS, and Windows
- **Type-Safe API**: Type hints and type-safe inference method selection
- **Flexible Input**: Supports both `Path` objects and string paths
- **Performance Optimized**: Hybrid inference combines Magic and Magika when it improves the result
- **Well-Tested**: Comprehensive automated test suite
- **Extensible**: Base class architecture for custom inferencer implementations

## Installation

### Python Package

```bash
pip install filetype-detector
```

Or using rye:

```bash
rye sync
```

### Interactive Terminal Demo

Use the installed terminal interface to filter a directory live and compare
Lexical, Magic, Magika, and Hybrid results for the selected file:

```bash
filetype-detector-demo path/to/files
```

`python -m filetype_detector path/to/files` is equivalent. The directory is
optional and defaults to the current working directory.

### System Dependencies

**Important**: `MagicInferencer` and `HybridInferencer` require the `libmagic` system library to be installed.

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install libmagic1
```

#### Fedora/RHEL/CentOS

```bash
sudo dnf install file-libs
# or for older versions:
# sudo yum install file-libs
```

#### Arch Linux

```bash
sudo pacman -S file
```

#### macOS

Using Homebrew:

```bash
brew install libmagic
```

Using MacPorts:

```bash
sudo port install file
```

#### Windows

Windows users need to use `python-magic-bin` as an alternative:

```bash
pip install python-magic-bin
```

Or download `libmagic` DLL manually from [file.exe releases](https://github.com/julian-r/file-windows/releases).

#### Alpine Linux (Docker)

```bash
apk add --no-cache file
```

#### Verification

After installation, verify `libmagic` is available:

```bash
file --version
```

If the command works, `libmagic` is properly installed.

#### TikaInferencer

`TikaInferencer` uses a pinned Apache Tika build instead of `libmagic`, so its
labels do not drift between operating systems. It needs two things that
`pip install` does not provide:

1. **Java 11 or newer** on `PATH` (`java -version` should work).
2. **The pinned `tika-app-3.3.3.jar`**. Download it once before the first
   `detect()` call:

   ```python
   from filetype_detector import TikaInferencer

   TikaInferencer.download_jar()  # fetches from Maven Central, verifies SHA-512
   ```

   The JAR is stored at `~/.cache/filetype-detector/tika-app-3.3.3.jar` and
   reused. To use your own copy, set the `TIKA_JAR` environment variable or
   pass `jar_path=` to the constructor. The SHA-512 of the JAR is checked
   against a pinned value on every run; a mismatched JAR is refused.

`detect()` raises `FileNotFoundError` if the JAR is missing and `RuntimeError`
if Java is not installed. No automatic download happens at detection time:
identical labels on every OS require the identical, verified JAR.


## Quick Start

**Recommended**: Use `UnifiedInferencer` with `backend="hybrid"` for the best balance of performance and accuracy:

Content-based backends require the supplied path to reference an existing file.

```python
from filetype_detector import UnifiedInferencer

inferencer = UnifiedInferencer(backend="hybrid")
ft = inferencer.detect("document.pdf")
'.pdf' in ft.extensions   # True
ft.mime_types             # ('application/pdf',)
```

All `detect()` methods return a `FileType` instance. See [FileType](#filetype) for details.

For more examples and usage patterns, see the [documentation site](https://devcomfort.github.io/file_type_detector/).

## FileType

`detect()` returns `FileType`, a frozen dataclass that keeps extensions and
MIME types together:

```python
from filetype_detector import FileType

ft = FileType.from_extension('.pdf')
ft.extensions   # ('.pdf',)
ft.mime_types   # ('application/pdf',)

ft2 = FileType.from_mimetype('image/jpeg')
ft2.extensions  # ('.jfif', '.jpe', '.jpeg', '.jpg') – may differ per OS
```

| Property | Type | Description |
|----------|------|-------------|
| `extensions` | `tuple[str, ...]` | Associated file extensions |
| `mime_types` | `tuple[str, ...]` | Associated MIME types |

Factory methods: `FileType.from_extension(ext)`, `FileType.from_mimetype(mime)`

## Performance Comparison

Choose the right inferencer based on your needs:

| Inferencer | Avg. Time (per file) | Memory | Throughput | Best For |
|------------|---------------------|--------|------------|----------|
| **LexicalInferencer** | < 0.001ms | Minimal | 50,000+ files/sec | Trusted extensions |
| **MagicInferencer** | ~1-5ms | Low | 200-500 files/sec | Content-based detection |
| **MagikaInferencer** | ~5-10ms* | High** | 100-200 files/sec | Highest accuracy (text) |
| **TikaInferencer** | ~1-5ms*** | Medium | 200-500 files/sec | OS-independent labels |
| **HybridInferencer** | ~1-6ms | Medium | 150-400 files/sec | **⭐ Recommended default** |

\* After initial model load (~100-200ms one-time overhead)  
\*\* Model loaded into memory (~50-100MB)  
\*\*\* After one-time JVM + JAR startup; the Java process stays alive between calls

### Recommendation

**For most use cases**: Use `UnifiedInferencer(backend="hybrid")` - it delegates to `HybridInferencer`, which automatically uses Magic for binary files and Magika for text files.

See [Choosing an Inferencer](#choosing-an-inferencer) for a full decision guide and known limitations per inferencer.

## Available Inferencers

### LexicalInferencer

Fastest method - extracts file extensions directly from paths without reading file contents.

```python
from filetype_detector import LexicalInferencer

inferencer = LexicalInferencer()
ft = inferencer.detect("document.pdf")
'.pdf' in ft.extensions   # True

inferencer.detect("file_without_ext")  # Raises ValueError
```

### MagicInferencer

Uses `python-magic` (libmagic) to detect file types based on magic numbers and file signatures.

```python
from filetype_detector import MagicInferencer

inferencer = MagicInferencer()
ft = inferencer.detect("file.dat")   # reads file content, ignores extension
ft.extensions                        # e.g. ('.pdf',) even if the name says .dat
ft.mime_types                        # e.g. ('application/pdf',)
```

**System Requirements**: Requires `libmagic` system library. See [Installation](#installation) section.

### MagikaInferencer

AI-powered detection with confidence scores. Especially effective for text files.

```python
from filetype_detector import MagikaInferencer

inferencer = MagikaInferencer()
ft = inferencer.detect("script.py")
'.py' in ft.extensions   # True

# detect_with_score returns (str, float), not FileType
extension, score = inferencer.detect_with_score("data.json")  # ('.json', 0.98)
```

### TikaInferencer

Uses Apache Tika instead of `libmagic`. A pinned Tika build returns identical
MIME and extension labels on Linux, macOS, and Windows, so the labels do not
depend on the operating system's MIME database or libmagic version.

```python
from filetype_detector import TikaInferencer

TikaInferencer.download_jar()  # one-time: verified tika-app-3.3.3.jar

inferencer = TikaInferencer()
ft = inferencer.detect("file.dat")
ft.mime_types   # e.g. ('application/pdf',), identical on every OS
ft.extensions   # e.g. ('.pdf',), identical on every OS
```

Detection runs in a long-lived Java process started lazily on the first call.
JVM startup is paid once; later calls are fast.

**System Requirements**: Java 11+ and the pinned JAR. See
[System Dependencies](#system-dependencies).

### HybridInferencer

Smart two-stage approach: uses Magic for all files, then Magika for text files.

```python
from filetype_detector import HybridInferencer

inferencer = HybridInferencer()

# Text file: Magic detects text/plain, then Magika refines to .py
ft = inferencer.detect("script.py")
'.py' in ft.extensions   # True

# Binary file: Magic result is used directly, Magika is skipped
ft = inferencer.detect("document.pdf")
'.pdf' in ft.extensions  # True
```

If you want the same behavior through the unified interface, use `UnifiedInferencer(backend="hybrid")`.

**System Requirements**: Requires `libmagic` system library. See [Installation](#installation) section.

## Choosing an Inferencer

Pick the inferencer that matches the files you expect and the guarantees you
need:

```
Do you trust the file name (extension)?
├─ Yes → LexicalInferencer   (no file reads, fastest)
└─ No / unsure
       ├─ Need identical labels on every OS?
       │       └─ TikaInferencer      (pinned Tika, needs Java + JAR)
       ├─ Mostly binary? (PDF, Office, images, archives)
       │       └─ MagicInferencer
       ├─ Mostly text? (Python, JSON, HTML, CSV)
       │       └─ MagikaInferencer    (finer classes + confidence score)
       └─ Mixed / undecided
               └─ HybridInferencer   (recommended default)
```

| Situation | Recommended |
|-----------|-------------|
| Already-cleaned files, e.g. CI pipelines | `LexicalInferencer` |
| Missing or suspicious extensions | `MagicInferencer` |
| Fine-grained text types (`.py` / `.json` / `.csv`) | `MagikaInferencer` |
| Confidence scores (`detect_with_score`) | `MagikaInferencer` |
| Identical MIME/extension labels across OS | `TikaInferencer` |
| Unknown uploads where anything may arrive | `HybridInferencer` |
| One entry point, swap backends by name | `UnifiedInferencer` |

## Known Limitations

### LexicalInferencer

Cannot detect files without an extension or with a wrong one. It never reads
file contents, so forged files pass through unchanged.

### MagicInferencer

Cannot distinguish subtypes of `text/plain`: Python, JSON, and CSV all return
`text/plain`. Compound Document formats (legacy `.doc`, `.ppt`, `.xls`) share
one container, so several extensions may be returned as candidates.
MIME-to-extension mapping comes from the OS `mimetypes` database, so extension
sets can differ between systems.

### MagikaInferencer

- **Limited benefit outside text files.** On binary files it performs the same
  as or worse than `MagicInferencer`.
- **HWP**: not in the training data; returns an empty result.
- **ZIP-based formats** (HWPX, ODF, ePub, etc.): does not inspect the internal
  structure and may misclassify, e.g. as `.epub`.
- **Model loading cost**: 100–200ms overhead on the first instantiation.

### TikaInferencer

- Requires Java 11+ and a separately downloaded JAR; detection fails fast with
  `FileNotFoundError` or `RuntimeError` if either is missing.
- The first `detect()` call pays JVM startup cost; keep one instance alive for
  repeated calls.
- The real filename is sent to Tika as a hint, so detection is not purely
  content-based when a misleading name is present.

### HybridInferencer

Calls Magika only when the Magic result starts with `text/`. ZIP-based formats
(HWPX, ODF, etc.) and Compound Document formats are handled by Magic alone.

## Documentation

- Tutorial: [Getting Started](https://devcomfort.github.io/file_type_detector/getting-started/)
- How-to Guides: choosing an inferencer, bulk processing, and extending the library
- Reference: API pages for `UnifiedInferencer`, `BaseInferencer`, and each inferencer
- Explanation: inference strategy trade-offs and architecture notes

For detailed usage examples, error handling, and advanced patterns, see the [documentation site](https://devcomfort.github.io/file_type_detector/).

## Testing

### Reviewed Ground Truth

Candidate review data lives in
`tests/truth/backend_inventory_candidates.json`. Collectors evaluate only the
matching verified records in `tests/truth/backend_inventory.json`. The reviewed
three-platform semantic baseline lives in
`tests/truth/backend_conformance_baseline.json`.

Validate the inventory pair before collecting observations:

```bash
rye run python -m scripts.conformance.cli review \
  --candidates tests/truth/backend_inventory_candidates.json \
  --inventory tests/truth/backend_inventory.json \
  --root . \
  --require-complete
```

### Conformance Tests

Run the inventory, collector, evaluator, report, and baseline contracts:

```bash
rye run python -m pytest tests/conformance -q
```

The dedicated
[Backend conformance workflow](https://github.com/devcomfort/file_type_detector/actions/workflows/backend-conformance.yml)
collects fresh-process observations on Ubuntu, macOS, and Windows. See the
[Backend Conformance reference](docs/reference/backend-conformance.md) for
local collection and aggregation commands.

### Behavior Tests

Delegation correctness:

```bash
rye run python -m pytest tests/test_unified_inferencer.py -v
```

Inferencer control flow, errors, and fallbacks:

```bash
rye run python -m pytest tests/test_magic_inferencer.py tests/test_magika_inferencer.py tests/test_hybrid_inferencer.py -v
```

### Full Verification

```bash
rye sync && \
rye run python -m scripts.conformance.cli review \
  --candidates tests/truth/backend_inventory_candidates.json \
  --inventory tests/truth/backend_inventory.json \
  --root . \
  --require-complete && \
rye run python -m pytest && \
rye run ruff check src tests scripts examples && \
rye run mypy src/filetype_detector scripts/conformance --ignore-missing-imports && \
rye run mkdocs build --strict
```

## Architecture

### Base Class

All inferencers inherit from `BaseInferencer`, which defines a common interface:

```python
from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path
from filetype_detector import FileType

class BaseInferencer(ABC):
    @abstractmethod
    def detect(self, file_path: Union[Path, str]) -> FileType:
        """Infer file type from path. Returns a FileType instance."""
        raise NotImplementedError
```

### Custom Inferencer

You can create custom inferencers by subclassing `BaseInferencer`:

```python
from filetype_detector import BaseInferencer, FileType
from typing import Union
from pathlib import Path

class CustomInferencer(BaseInferencer):
    def detect(self, file_path: Union[Path, str]) -> FileType:
        # Your custom logic here
        return FileType.from_extension(".custom")
```

## Dependencies

Runtime dependencies:

- `python-magic>=0.4.27`: Magic-number file detection
- `magika>=1.0.1`: AI-powered content detection
- `rich>=14.2.0`: Styled inference output
- `textual>=8.2.8`: Interactive terminal interface

Development, documentation, and fixture-generation packages are isolated in
the `dev`, `docs`, and `fixtures` optional extras.

## Requirements

- Python >= 3.10
- For `MagicInferencer` / `HybridInferencer`: `libmagic` (see [System Dependencies](#system-dependencies))
- For `TikaInferencer`: Java 11+ and the pinned JAR (see [System Dependencies](#system-dependencies))

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest tests/ -v`
2. Code follows the existing style
3. New features include appropriate tests
4. Documentation is updated

## Acknowledgments

- [python-magic](https://github.com/ahupp/python-magic) for libmagic bindings
- [Google Magika](https://github.com/google/magika) for AI-powered file type detection
- [Apache Tika](https://tika.apache.org/) for OS-independent content detection
