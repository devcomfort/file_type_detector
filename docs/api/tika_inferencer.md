# TikaInferencer

Detects file types with a pinned Apache Tika build in a long-lived JVM process.
A pinned build returns identical MIME and extension labels on Linux, macOS, and
Windows, so results do not depend on the OS MIME database.

```python
from filetype_detector import TikaInferencer
```

## Requirements

- Java 11+ on `PATH`.
- The pinned `tika-app-3.3.3.jar`. Resolve it with an explicit `jar_path`, the
  `TIKA_JAR` environment variable, or the default cache path
  `~/.cache/filetype-detector/tika-app-3.3.3.jar`. Verify or fetch it once with
  `TikaInferencer.download_jar()`; the SHA-512 is checked before first use.

The pinned version, JAR URL, and SHA-512 are read from `tika-manifest.json`
at the repository root (or the `FILETYPE_TIKA_MANIFEST` override). The
`scripts/install-tika-tools-{linux,macos}.sh` and `-windows.ps1` helpers
install Java via jabba and fetch the verified JAR.

## Basic Usage

```python
from filetype_detector import TikaInferencer

inferencer = TikaInferencer()
ft = inferencer.detect("document.pdf")
ft.extensions  # ('.pdf',)
ft.mime_types  # ('application/pdf',)
```

The JVM is started lazily on the first `detect()` and reused for later calls,
so the startup cost is paid once. Use `close()` or the context manager to shut
it down explicitly.

## When to Use

- Results must be identical on Linux, macOS, and Windows.
- You can meet the Java and JAR requirements.
- `UnifiedInferencer(backend="tika")` gives the same behavior through the
  single entry point.

## Exceptions

- `FileNotFoundError`: the file or the verified JAR does not exist.
- `ValueError`: the path is not a file, or the JAR fails SHA-512 verification.
- `RuntimeError`: Java is unavailable, the probe exits, or Tika reports a
  detection error.
