# Getting Started

This tutorial takes you from installation to the first successful file type detection.

## Installation

### Using pip

```bash
pip install filetype-detector
```

### Using rye

If you're using rye for dependency management:

```bash
rye sync
```

### Interactive terminal demo

Browse any directory with a live filename filter and side-by-side strategy
results:

```bash
filetype-detector-demo path/to/files
```

`python -m filetype_detector path/to/files` launches the same interface. Omit
the directory to browse the current working directory.

## System Requirements

### Python

- Python >= 3.10

### System Libraries

**Important**: `MagicInferencer` and `HybridInferencer` require the `libmagic` system library. Install it based on your operating system:

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

**Using Homebrew (Recommended):**
```bash
brew install libmagic
```

**Using MacPorts:**
```bash
sudo port install file
```

#### Windows

Windows doesn't have native `libmagic` support. Use `python-magic-bin`:

```bash
pip install python-magic-bin
```

Alternatively, download the `libmagic` DLL manually from:
- [file.exe Windows releases](https://github.com/julian-r/file-windows/releases)

#### Alpine Linux (Common in Docker)

```bash
apk add --no-cache file
```

#### Verify Installation

After installation, verify `libmagic` is available:

```bash
file --version
```

You should see output like: `file-5.x`

If this command works, `libmagic` is properly installed and `MagicInferencer` will work correctly.

## Basic Usage

### Recommended: HybridInferencer

For most use cases, start with `AutoInferencer(backend="hybrid")` - it provides a single entry point with the same balanced behavior as `HybridInferencer`:

Content-based backends require the supplied path to reference an existing file.

```python
from filetype_detector import AutoInferencer

inferencer = AutoInferencer(backend="hybrid")
file_type = inferencer.infer("document.pdf")
'.pdf' in file_type.extensions  # True
```

### Using Individual Inferencers

You can also use inferencer classes directly:

```python
from filetype_detector import MagicInferencer

inferencer = MagicInferencer()
file_type = inferencer.infer("document.pdf")
print(file_type.extensions)  # Output: ('.pdf',)
```

### Using AutoInferencer

For type-safe backend selection, use `AutoInferencer`:

```python
from filetype_detector import AutoInferencer

magic = AutoInferencer(backend="magic")
file_type = magic.infer("file_without_ext")
print(file_type.extensions)
```

See [Examples and Patterns](user-guide.md) for longer examples and [AutoInferencer](api/auto_inferencer.md) for backend selection details.

## Next Steps

- Read the [How-to Guides](how-to/index.md) when you want to solve a specific task
- Browse [Examples and Patterns](user-guide.md) for reusable snippets and larger examples
- Use the [Reference Overview](reference/index.md) when you need exact API details
- Read the [Explanation Overview](explanation/index.md) for design rationale and trade-offs

