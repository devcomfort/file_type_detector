# filetype-detector

[![Formats Tested](https://img.shields.io/badge/formats-598%20tested-brightgreen)]()
[![Magic](https://img.shields.io/badge/magic-59.9%25-blue)]()
[![Magika](https://img.shields.io/badge/magika-62.5%25-green)]()
[![Hybrid](https://img.shields.io/badge/hybrid-74.2%25-purple)]()

A Python library for detecting file types using multiple inference strategies, including path-based extraction, magic number detection, and AI-powered content analysis.

## Accuracy

| Metric | Value |
|--------|-------|
| Magic (libmagic) correct | **59.9%** |
| Magika (Google AI) correct | **62.5%** |
| Hybrid (runtime strategy) | **74.2%** |
| Total file formats | **598** |

![Accuracy Venn Diagram](docs/diagrams/accuracy-venn.svg)

> Generated from 598 canonical fixtures. See [Accuracy Benchmarks](docs/reference/accuracy-benchmarks.md) for per-format data.

## Features

- **Multiple Inference Methods**: Choose from lexical, magic-based, AI-powered, or hybrid inference strategies
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

## Quick Start

**Recommended**: Use `AutoInferencer` with `backend="hybrid"` for the best balance of performance and accuracy:

Content-based backends require the supplied path to reference an existing file.

```python
from filetype_detector import AutoInferencer

inferencer = AutoInferencer(backend="hybrid")
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions   # True
ft.mime_types             # ('application/pdf',)
```

All `infer()` methods return a `FileType` instance. See [FileType](#filetype) for details.

For more examples and usage patterns, see the [documentation site](https://devcomfort-labs.github.io/file_type_detector/).

## FileType

`infer()`가 반환하는 `FileType`은 frozen dataclass로, 확장자와 MIME 타입을 함께 보관한다.

```python
from filetype_detector import FileType

ft = FileType.from_extension('.pdf')
ft.extensions   # ('.pdf',)
ft.mime_types   # ('application/pdf',)

ft2 = FileType.from_mimetype('image/jpeg')
ft2.extensions  # ('.jfif', '.jpe', '.jpeg', '.jpg') – OS별로 다를 수 있음
```

| 프로퍼티 | 타입 | 설명 |
|---------|------|------|
| `extensions` | `tuple[str, ...]` | 연관된 파일 확장자 목록 |
| `mime_types` | `tuple[str, ...]` | 연관된 MIME 타입 목록 |

팩토리 메서드: `FileType.from_extension(ext)`, `FileType.from_mimetype(mime)`

## Performance Comparison

Choose the right inferencer based on your needs:

| Inferencer | Avg. Time (per file) | Memory | Throughput | Best For |
|------------|---------------------|--------|------------|----------|
| **LexicalInferencer** | < 0.001ms | Minimal | 50,000+ files/sec | Trusted extensions |
| **MagicInferencer** | ~1-5ms | Low | 200-500 files/sec | Content-based detection |
| **MagikaInferencer** | ~5-10ms* | High** | 100-200 files/sec | Highest accuracy (text) |
| **HybridInferencer** | ~1-6ms | Medium | 150-400 files/sec | **⭐ Recommended default** |

\* After initial model load (~100-200ms one-time overhead)  
\*\* Model loaded into memory (~50-100MB)

### Recommendation

**For most use cases**: Use `AutoInferencer(backend="hybrid")` - it delegates to `HybridInferencer`, which automatically uses Magic for binary files and Magika for text files.

See [Choosing an Inferencer](#choosing-an-inferencer) for a full decision guide and known limitations per inferencer.

## Available Inferencers

### LexicalInferencer

Fastest method - extracts file extensions directly from paths without reading file contents.

```python
from filetype_detector import LexicalInferencer

inferencer = LexicalInferencer()
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions   # True

inferencer.infer("file_without_ext")  # Raises ValueError
```

### MagicInferencer

Uses `python-magic` (libmagic) to detect file types based on magic numbers and file signatures.

```python
from filetype_detector import MagicInferencer

inferencer = MagicInferencer()
ft = inferencer.infer("file.dat")   # reads file content, ignores extension
ft.extensions                        # e.g. ('.pdf',) even if the name says .dat
ft.mime_types                        # e.g. ('application/pdf',)
```

**System Requirements**: Requires `libmagic` system library. See [Installation](#installation) section.

### MagikaInferencer

AI-powered detection with confidence scores. Especially effective for text files.

```python
from filetype_detector import MagikaInferencer

inferencer = MagikaInferencer()
ft = inferencer.infer("script.py")
'.py' in ft.extensions   # True

# infer_with_score returns (str, float), not FileType
extension, score = inferencer.infer_with_score("data.json")  # ('.json', 0.98)
```

### HybridInferencer

Smart two-stage approach: uses Magic for all files, then Magika for text files.

```python
from filetype_detector import HybridInferencer

inferencer = HybridInferencer()

# Text file: Magic detects text/plain, then Magika refines to .py
ft = inferencer.infer("script.py")
'.py' in ft.extensions   # True

# Binary file: Magic result is used directly, Magika is skipped
ft = inferencer.infer("document.pdf")
'.pdf' in ft.extensions  # True
```

If you want the same behavior through the unified interface, use `AutoInferencer(backend="hybrid")`.

**System Requirements**: Requires `libmagic` system library. See [Installation](#installation) section.

## Choosing an Inferencer

파일 성격과 요구사항에 따라 추론기를 선택한다.

```
파일 이름(확장자)을 신뢰할 수 있는가?
├─ 예  → LexicalInferencer   (파일 읽기 없음, 가장 빠름)
└─ 아니오 / 불확실
       ├─ 주로 바이너리? (PDF, Office, 이미지, 압축 등)
       │       └─ MagicInferencer
       ├─ 주로 텍스트? (Python, JSON, HTML, CSV 등)
       │       └─ MagikaInferencer   (세부 분류 + 신뢰도 점수)
       └─ 혼합 / 미확정
               └─ HybridInferencer  (기본값 추천)
```

| 상황 | 추천 |
|------|------|
| CI 파이프라인 등 이미 정제된 파일 | `LexicalInferencer` |
| 확장자 없는 파일, 잘못된 확장자 검증 | `MagicInferencer` |
| `.py` / `.json` / `.csv` 등 텍스트 세분화 | `MagikaInferencer` |
| 신뢰도 점수(`infer_with_score`)가 필요할 때 | `MagikaInferencer` |
| 업로드 파일 등 무엇이 올지 모를 때 | `HybridInferencer` |
| 단일 진입점으로 backend만 교체하고 싶을 때 | `AutoInferencer` |

## Known Limitations

### LexicalInferencer

확장자가 없거나 잘못된 경우 탐지 불가. 파일 내용을 읽지 않으므로 위변조 파일을 그대로 통과시킨다.

### MagicInferencer

`text/plain`으로 분류되는 파일들의 세부 구분이 불가능하다. Python, JSON, CSV 등이 동일하게 `text/plain`을 반환한다.
Compound Document 포맷(구 `.doc`, `.ppt`, `.xls`)은 같은 컨테이너를 공유하므로 여러 확장자가 후보로 반환된다.

### MagikaInferencer

- **텍스트 파일 외에는 이점이 제한적이다.** 바이너리 파일에서는 `MagicInferencer`와 동등하거나 열등한 경우가 있다.
- **HWP**: 학습 데이터에 없어 빈 결과를 반환한다.
- **ZIP 기반 포맷** (HWPX, ODF, ePub 등): 내부 구조를 분석하지 않아 `.epub` 등으로 오분류될 수 있다.
- **모델 로딩 비용**: 첫 인스턴스화 시 100–200ms의 오버헤드가 있다.

### HybridInferencer

Magic 결과가 `text/`로 시작할 때만 Magika를 호출한다.
ZIP 기반 포맷(HWPX, ODF 등)과 Compound Document 포맷은 Magic으로만 처리되며 Magika가 적용되지 않는다.

## Key Features

- ✅ **Multiple inference strategies** - Choose the right method for your use case
- ✅ **Type-safe API** - Full type hints and type-safe method selection
- ✅ **Flexible input** - Supports both `Path` objects and string paths
- ✅ **Performance optimized** - Hybrid inference combines fast binary detection with more detailed text detection
- ✅ **Well-tested** - Comprehensive test suite
- ✅ **Extensible** - Base class architecture for custom implementations

## Documentation

- Tutorial: [Getting Started](https://devcomfort-labs.github.io/file_type_detector/getting-started/)
- How-to Guides: choosing an inferencer, bulk processing, and extending the library
- Reference: API pages for `AutoInferencer`, `BaseInferencer`, and each inferencer
- Explanation: inference strategy trade-offs and architecture notes

For detailed usage examples, error handling, and advanced patterns, see the [documentation site](https://devcomfort-labs.github.io/file_type_detector/).

## Testing

### Truth data

Canonical fixture truth lives in `tests/truth/canonical_fixtures.json`.
Tool snapshots (version-pinned per-inferencer results) live in
`tests/truth/tool_snapshots.json`.

Regenerate truth data after adding fixtures:

```bash
# Rebuild tool snapshots from canonical fixtures
rye run python scripts/generate_truth_data.py

# Check that existing snapshots match without overwriting
rye run python scripts/generate_truth_data.py --check
```

### Accuracy suites

Cross-suite smoke test (representative sample across all 598 canonical fixtures):

```bash
rye run python -m pytest tests/test_file_type_truth.py tests/test_fixture_coverage.py -v
```

Per-inferencer accuracy (semantic + snapshot contracts):

```bash
rye run python -m pytest tests/test_accuracy_magic.py tests/test_accuracy_magika.py tests/test_accuracy_hybrid.py -v
```

Delegation correctness (AutoInferencer matches direct inferencer):

```bash
rye run python -m pytest tests/test_auto_inferencer.py -v
```

Behavior tests (control flow, mocks, error handling):

```bash
rye run python -m pytest tests/test_magic_inferencer.py tests/test_magika_inferencer.py tests/test_hybrid_inferencer.py -v
```

### Full verification

One command to run the complete verification pipeline — truth check, all tests, lint, and type-check:

```bash
rye sync && rye run python scripts/generate_truth_data.py --check && rye run python -m pytest && rye run ruff check src tests scripts examples && rye run mypy src/filetype_detector/ --ignore-missing-imports
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
    def infer(self, file_path: Union[Path, str]) -> FileType:
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
    def infer(self, file_path: Union[Path, str]) -> FileType:
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
