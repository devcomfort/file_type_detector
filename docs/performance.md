# Performance Guide

Understanding performance characteristics of different inferencers and how to optimize usage.

## Performance Comparison

### Benchmark Overview

| Inferencer | Avg. Time (per file) | Memory | Use Case |
|------------|---------------------|--------|----------|
| LexicalInferencer | < 0.001ms | Minimal | Fastest, no I/O |
| MagicInferencer | ~1-5ms | Low | Fast content-based |
| MagikaInferencer | ~5-10ms* | High** | AI-powered detection |
| CascadingInferencer | ~1-6ms | Medium | Balanced approach |

\* After initial model load (~100-200ms one-time overhead)  
\*\* Model loaded into memory (~50-100MB)

### Detailed Breakdown

#### LexicalInferencer

- **Speed**: Fastest (~microseconds per file)
- **I/O**: None (pure string manipulation)
- **Memory**: Minimal
- **Best for**: High-volume processing where extensions are trusted

```python
from file_type_infer.lexical_inferencer import LexicalInferencer

inferencer = LexicalInferencer()

# Processes thousands of files per second
for file_path in large_file_list:
    extension = inferencer.infer(file_path)  # Instant
```

#### MagicInferencer

- **Speed**: Fast (~1-5ms per file)
- **I/O**: Reads file headers (first few KB)
- **Memory**: Low
- **Best for**: Content-based detection without AI overhead

```python
from file_type_infer.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()

# Processes hundreds of files per second
for file_path in file_list:
    extension = inferencer.infer(file_path)  # Fast content analysis
```

#### MagikaInferencer

- **Speed**: Slower (~5-10ms per file after model load)
- **I/O**: Reads file content (limited subset)
- **Memory**: High (model in memory)
- **Model Load**: One-time ~100-200ms overhead
- **Best for**: Highest accuracy, especially text files

```python
from file_type_infer.magika_inferencer import MagikaInferencer

inferencer = MagikaInferencer()  # Model loads here (~100-200ms)

# Processes 100-200 files per second
for file_path in file_list:
    extension = inferencer.infer(file_path)  # AI inference
```

#### CascadingInferencer

- **Speed**: Balanced (~1-6ms per file)
  - Binary files: ~1-5ms (Magic only)
  - Text files: ~5-10ms (Magic + Magika)
- **I/O**: Same as Magic + Magika for text
- **Memory**: Medium (Magika model in memory)
- **Best for**: General-purpose use with mixed file types

```python
from file_type_infer.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()  # Magika model loads here

# Automatically optimizes per file type
for file_path in mixed_file_list:
    extension = inferencer.infer(file_path)
    # Fast for binaries, precise for text files
```

## Optimization Strategies

### 1. Reuse Inferencer Instances

**Bad:**
```python
for file_path in files:
    inferencer = MagicInferencer()  # Creates new instance each time
    extension = inferencer.infer(file_path)
```

**Good:**
```python
inferencer = MagicInferencer()  # Create once
for file_path in files:
    extension = inferencer.infer(file_path)
```

### 2. Choose the Right Inferencer

**For high-volume processing with trusted extensions:**
```python
from file_type_infer.lexical_inferencer import LexicalInferencer

inferencer = LexicalInferencer()  # Fastest
```

**For content-based detection:**
```python
from file_type_infer.magic_inferencer import MagicInferencer

inferencer = MagicInferencer()  # Good balance
```

**For mixed content (recommended):**
```python
from file_type_infer.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()  # Optimizes automatically
```

### 3. Batch Processing

For large batches, consider parallel processing:

```python
from concurrent.futures import ThreadPoolExecutor
from file_type_infer.mixture_inferencer import CascadingInferencer
from pathlib import Path

def detect_type(file_path: Path) -> tuple[str, str]:
    inferencer = CascadingInferencer()
    try:
        ext = inferencer.infer(file_path)
        return (str(file_path), ext)
    except Exception as e:
        return (str(file_path), f"Error: {e}")

# Parallel processing
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(detect_type, file_list))
```

### 4. Lazy Loading for Magika

If using MagikaInferencer sparingly:

```python
from file_type_infer.magika_inferencer import MagikaInferencer

class LazyMagikaInferencer:
    def __init__(self):
        self._inferencer = None
    
    @property
    def inferencer(self):
        if self._inferencer is None:
            self._inferencer = MagikaInferencer()
        return self._inferencer
    
    def infer(self, file_path):
        return self.inferencer.infer(file_path)

# Model only loads when first used
lazy = LazyMagikaInferencer()
```

## Memory Considerations

### MagikaInferencer Model

The Magika model is loaded into memory when the inferencer is instantiated:
- **Model Size**: ~50-100MB
- **Load Time**: ~100-200ms (one-time)
- **Memory**: Persistent while inferencer instance exists

**Best Practice**: Create one MagikaInferencer instance and reuse it.

### Memory Usage Patterns

```python
# High memory - one instance per file
for file_path in files:
    inferencer = MagikaInferencer()  # Don't do this!
    extension = inferencer.infer(file_path)

# Optimal - one instance for all files
inferencer = MagikaInferencer()
for file_path in files:
    extension = inferencer.infer(file_path)
```

## Throughput Estimates

Based on typical hardware:

### LexicalInferencer
- **Throughput**: 50,000+ files/second
- **Bottleneck**: None (pure CPU)

### MagicInferencer
- **Throughput**: 200-500 files/second
- **Bottleneck**: File I/O and magic number detection

### MagikaInferencer
- **Throughput**: 100-200 files/second
- **Bottleneck**: AI inference
- **Note**: First inference slower due to model load

### CascadingInferencer
- **Throughput**: 150-400 files/second (depends on text/binary ratio)
- **Bottleneck**: File I/O + conditional Magika inference

## Caching Strategies

For repeated file type detection, consider caching:

```python
from functools import lru_cache
from file_type_infer.magic_inferencer import MagicInferencer

class CachedMagicInferencer(MagicInferencer):
    @lru_cache(maxsize=1000)
    def infer(self, file_path):
        # Convert to string for cache key
        return super().infer(str(file_path) if not isinstance(file_path, str) else file_path)

inferencer = CachedMagicInferencer()
# Subsequent calls with same file path use cache
```

## Profiling Your Usage

Use Python's profiling tools to identify bottlenecks:

```python
import cProfile
from file_type_infer.mixture_inferencer import CascadingInferencer

inferencer = CascadingInferencer()

cProfile.run("""
for file_path in file_list:
    inferencer.infer(file_path)
""")
```

