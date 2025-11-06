# Getting Started

This guide will help you get started with `file-type-infer` quickly.

## Installation

### Using pip

```bash
pip install file-type-infer
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

### Using the Inferencer Map

The easiest way to use `file-type-infer` is through the centralized `FILE_FORMAT_INFERENCER_MAP`:

```python
from file_type_infer.inferencer import FILE_FORMAT_INFERENCER_MAP

# Lexical inference (fastest)
lexical = FILE_FORMAT_INFERENCER_MAP[None]
extension = lexical("document.pdf")  # Returns: '.pdf'

# Magic inference (content-based)
magic = FILE_FORMAT_INFERENCER_MAP["magic"]
extension = magic("file_without_ext")  # Returns detected type

# Magika inference (AI-powered)
magika = FILE_FORMAT_INFERENCER_MAP["magika"]
extension = magika("script.py")  # Returns: '.py'
```

### Using Individual Inferencers

You can also use inferencer classes directly:

```python
from file_type_infer.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()
extension = inferencer.infer("document.pdf")
print(extension)  # Output: '.pdf'
```

### Type-Safe Usage

The library provides type hints for better IDE support:

```python
from file_type_infer.inferencer import InferencerType, FILE_FORMAT_INFERENCER_MAP

def process_file(file_path: str, method: InferencerType) -> str:
    inferencer_func = FILE_FORMAT_INFERENCER_MAP[method]
    return inferencer_func(file_path)

# Type-safe calls
result = process_file("doc.pdf", "magic")  # ✅ Valid
result = process_file("doc.pdf", None)     # ✅ Valid
# result = process_file("doc.pdf", "invalid")  # ❌ Type error
```

## Choosing the Right Inferencer

| Inferencer | Speed | Accuracy | Use Case |
|------------|-------|----------|----------|
| `LexicalInferencer` | Fastest | Low | When extensions are trusted |
| `MagicInferencer` | Fast | High (binary) | General purpose, binary files |
| `MagikaInferencer` | Slower | Highest (text) | Text files, need confidence scores |
| `CascadingInferencer` | Balanced | High (all) | **Recommended default** |

### Recommended Approach

For most use cases, use `CascadingInferencer`:

```python
from file_type_infer.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()

# Automatically uses Magic for binaries, Magika for text files
extension = inferencer.infer("document.pdf")  # Fast Magic detection
extension = inferencer.infer("script.py")      # Magic + Magika for precision
```

## Next Steps

- Read the [User Guide](user-guide.md) for detailed usage instructions
- Check out [Examples](examples.md) for real-world use cases
- Explore the [API Reference](api/base.md) for complete documentation

