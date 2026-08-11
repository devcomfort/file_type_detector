# Inference Strategies

`filetype-detector` provides multiple inferencers because file type detection has no single best answer.
Some workloads need speed. Some need content validation. Some need finer distinctions between text formats.

## The Core Trade-off

The library balances three goals:

- speed
- reliability on wrong or missing extensions
- specificity for text formats

Each inferencer chooses a different point on that trade-off.

## `LexicalInferencer`

`LexicalInferencer` trusts the path.
It is fast because it never reads the file.
That makes it useful when file names are already trustworthy, but weak when extensions are wrong or missing.

## `MagicInferencer`

`MagicInferencer` trusts file signatures.
It uses libmagic to classify content from bytes and then maps MIME types to extensions.
This works well for binary formats and for files whose names are misleading.

## `MagikaInferencer`

`MagikaInferencer` uses a trained model.
It is most useful when you need finer distinctions between text-based formats such as Python, JSON, or CSV.
It also gives you confidence scores, which makes it the best choice when you need to filter weak predictions.

## `HybridInferencer`

`HybridInferencer` exists because the strengths of Magic and Magika are different.
Magic is a good first pass for all files. Magika is more useful when the file is text and the exact format matters.

So the hybrid strategy does this:

1. Use Magic first.
2. If the file looks like text, run Magika.
3. If Magika cannot help, keep the Magic result.

This keeps binary detection fast while improving text detection when it matters.

## `AutoInferencer`

`AutoInferencer` does not add a new detection algorithm.
Its job is to make backend selection uniform.
Instead of importing a different class for each strategy, callers can keep one public entry point and switch behavior with `backend`.

## Practical Takeaway

Choose `lexical` when names are reliable, `magic` when content validation matters, `magika` when text precision matters, and `hybrid` when you want one strong default for mixed workloads.

**Why Hybrid is the recommended default**: it preserves Magic's content result unless text or an ambiguous MIME makes Magika useful, then falls back when Magika has no result. The [backend conformance report](../reference/backend-conformance.md) verifies that control flow against reviewed facts for each supported runtime.

If you want the API details for each class, go to [Reference Overview](../reference/index.md).
If you want to apply the strategies to a concrete task, go to [How-to Guides](../how-to/index.md).