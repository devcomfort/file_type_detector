# Getting Started

This guide will help you get started with `filetype-detector` quickly.

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

## System Requirements

### Python

- Python >= 3.8

### System Libraries

**Important**: `MagicInferencer` and `CascadingInferencer` require the `libmagic` system library. Install it based on your operating system:

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

### Recommended: CascadingInferencer

For most use cases, start with `CascadingInferencer` - it provides the best balance of performance and accuracy:

```python
from filetype_detector.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()
extension = inferencer.infer("document.pdf")  # Returns: '.pdf'
```

### Using Individual Inferencers

You can also use inferencer classes directly:

```python
from filetype_detector.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()
extension = inferencer.infer("document.pdf")
print(extension)  # Output: '.pdf'
```

### Using the Inferencer Map

For type-safe method selection, use the centralized map:

```python
from filetype_detector.inferencer import FILE_FORMAT_INFERENCER_MAP

magic = FILE_FORMAT_INFERENCER_MAP["magic"]
extension = magic("file_without_ext")  # Returns detected type
```

See the [User Guide](user-guide.md) for detailed usage instructions and [Inferencer Map](api/inferencer-map.md) for type-safe selection patterns.

## Next Steps

- Read the [User Guide](user-guide.md) for comprehensive usage instructions, examples, and performance tips
- Explore the [API Reference](api/base.md) for complete API documentation

