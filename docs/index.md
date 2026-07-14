<div class="hero" markdown="1">
<p class="hero__eyebrow">Documentation</p>

# filetype-detector

<p class="hero__lead">Detect file types from paths, file signatures, or model-based analysis with one Python library and one consistent interface.</p>

<div class="hero__meta">
	<span class="hero__pill">Hybrid by default</span>
	<span class="hero__pill">Single `AutoInferencer` entry point</span>
	<span class="hero__pill">Reference + guides + explanations</span>
</div>

<div class="hero__actions" markdown="1">
[Start with the tutorial](getting-started.md){ .md-button .md-button--primary }
[Choose an inferencer](how-to/choose-an-inferencer.md){ .md-button }
[Browse the API reference](reference/index.md){ .md-button }
</div>
</div>

## Start Here

<div class="grid cards" markdown="1">

- __Getting Started__

	---

	Install the package, check system dependencies, and run the first successful detection.

	[Open the tutorial](getting-started.md)

- __Choose an Inferencer__

	---

	Pick the right backend for trusted extensions, content validation, text precision, or mixed workloads.

	[Open the guide](how-to/choose-an-inferencer.md)

- __Reference__

	---

	Look up exact API behavior for AutoInferencer, BaseInferencer, and each concrete inferencer.

	[Open reference overview](reference/index.md)

- __Explanation__

	---

	Understand the trade-offs behind lexical, magic, magika, and hybrid detection.

	[Open explanation overview](explanation/index.md)

</div>

## Quick Start

Content-based backends require the supplied path to reference an existing file.

```python
from filetype_detector import AutoInferencer

inferencer = AutoInferencer(backend="hybrid")
file_type = inferencer.infer("document.pdf")
'.pdf' in file_type.extensions  # True
```

## Quick Decision Guide

<div class="grid cards compact tight" markdown="1">

- __Need the fastest possible answer?__

	---

	Start with `LexicalInferencer`.

- __Need content-based validation?__

	---

	Start with `MagicInferencer`.

- __Need text precision or confidence scores?__

	---

	Start with `MagikaInferencer`.

- __Need one strong default for mixed files?__

	---

	Start with `AutoInferencer(backend="hybrid")`.

</div>

## Common Tasks

<div class="grid cards compact tight" markdown="1">

- __Choose the right backend__

	---

	[Choose an Inferencer](how-to/choose-an-inferencer.md)

- __Scan many files__

	---

	[Process Files in Bulk](how-to/process-files-in-bulk.md)

- __Add project-specific detection__

	---

	[Extend with a Custom Inferencer](how-to/extend-with-custom-inferencer.md)

- __Reuse working snippets__

	---

	[Examples and Patterns](user-guide.md)

</div>

## Requirements

- Python >= 3.10
- python-magic >= 0.4.27 for MagicInferencer and HybridInferencer
- magika >= 1.0.1 for MagikaInferencer and HybridInferencer
- rich >= 14.2.0 and textual >= 8.2.8 for the terminal demo

See [Getting Started](getting-started.md#system-requirements) for platform-specific system library installation instructions.
