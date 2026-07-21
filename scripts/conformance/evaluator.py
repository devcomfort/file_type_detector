"""Normalize detector output and compare it to reviewed Ground Truth."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from scripts.conformance.types import GroundTruth


def semantic_output(
    *, mime_types: Sequence[str], extensions: Sequence[str]
) -> dict[str, list[str]]:
    """Return lowercased, de-duplicated, sorted detector output."""
    return {
        "mime_types": sorted({mime_type.lower() for mime_type in mime_types}),
        "extensions": sorted(
            {_semantic_extension(extension) for extension in extensions}
        ),
    }


def _semantic_extension(extension: str) -> str:
    normalized = extension.lower()
    return normalized if normalized.startswith(".") else f".{normalized}"


def evaluate_output(
    *,
    semantic: Mapping[str, Sequence[str]],
    ground_truth: GroundTruth,
    status: str,
) -> dict[str, bool]:
    """Evaluate one semantic detector result against reviewed Ground Truth."""
    if status != "ok":
        return {
            "mime_match": False,
            "extension_match": False,
            "overall_match": False,
        }

    mime_match = bool(set(semantic["mime_types"]) & set(ground_truth.mimes))
    extension_match = bool(set(semantic["extensions"]) & set(ground_truth.extensions))
    return {
        "mime_match": mime_match,
        "extension_match": extension_match,
        "overall_match": mime_match and extension_match,
    }
