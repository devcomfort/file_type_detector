"""Shared factory for schema-v2 inventory test records.

Every conformance test that builds inventory/candidate documents should use
these helpers instead of hand-writing schema literals, so that the three
truth axes are always present and consistent.
"""

from __future__ import annotations

from typing import Any


def source_integrity_generated(
    *,
    generator_symbol: str = "scripts.generators",
    recipe_hash: str = "a" * 64,
    tier: str = "exact-byte",
) -> dict[str, Any]:
    return {
        "kind": "generated",
        "generator_symbol": generator_symbol,
        "recipe_hash": recipe_hash,
        "tier": tier,
    }


def format_validity_verified(
    validator: str = "test-structural-check/1.0",
) -> dict[str, Any]:
    return {
        "status": "verified",
        "validator": validator,
        "evidence": ["round-trip ok"],
    }


def gt_evidence(
    mime_types: list[str],
    extensions: list[str],
    *,
    authority: str = "test-authority",
    base_url: str = "https://registry.example.test",
) -> dict[str, Any]:
    return {
        "mime_claims": [
            {
                "mime_type": m,
                "authority": authority,
                "reference": f"{base_url}/{m.replace('/', '-')}",
            }
            for m in mime_types
        ],
        "extension_claims": [
            {
                "extension": e,
                "authority": authority,
                "reference": f"{base_url}/ext{e.replace('.', '-')}",
            }
            for e in extensions
        ],
    }


def complete_v2_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    """Add the three truth axes to a v1-style record, returning a v2-ready copy."""
    out = dict(record)
    gt = out.get("ground_truth", {})
    mimes = gt.get("mime_types", [])
    exts = gt.get("extensions", [])

    if "source_integrity" not in out:
        out["source_integrity"] = source_integrity_generated()
    if "format_validity" not in out:
        out["format_validity"] = format_validity_verified()
    if "ground_truth_evidence" not in out:
        out["ground_truth_evidence"] = gt_evidence(mimes, exts)
    return out
