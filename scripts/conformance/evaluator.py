"""Normalize MIME aliases and compare detector output to reviewed Ground Truth.

Three match levels are reported:
- exact: detected MIME/extension directly equals a GT entry
- alias: detected MIME is a documented true alias of a GT entry
- container: detected MIME is the parent container of the GT format
  (informational only; does NOT contribute to overall_match)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from scripts.conformance.types import GroundTruth

# True MIME aliases: both names refer to the same registered or de facto type.
# Only pairs with verifiable authority (IANA rename, vendor confirmation) belong here.
MIME_ALIASES: dict[str, str] = {
    "application/x-debian-package": "application/vnd.debian.binary-package",
    "application/x-x509-ca-cert": "application/pkix-cert",
    "text/x-markdown": "text/markdown",
}

# Reverse map for lookup convenience.
_ALIASES_REVERSE: dict[str, str] = {v: k for k, v in MIME_ALIASES.items()}

# Container relationships: parent container MIME -> set of child formats it can hold.
# A container match means the backend correctly identified the outer wrapper but
# missed the inner subtype. This is reported but does NOT count as overall_match.
CONTAINER_RELATIONS: dict[str, frozenset[str]] = {
    "application/zip": frozenset(
        {
            "application/vnd.android.package-archive",  # apk
            "application/java-archive",  # jar
            "application/epub+zip",  # epub
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    ),
    "application/octet-stream": frozenset(),  # generic fallback matches nothing specifically
    "text/plain": frozenset(
        {
            # text/plain is the fallback for all text/* subtypes, but detecting
            # text/plain when GT says text/x-python is NOT a container match —
            # it's a less specific answer. We do not treat it as partial credit.
        }
    ),
}


def canonical_mime(mime_type: str) -> str:
    """Return the canonical form of a MIME type by resolving known aliases."""
    return MIME_ALIASES.get(mime_type, mime_type)


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
) -> dict[str, object]:
    """Evaluate one semantic detector result against reviewed Ground Truth.

    Returns match booleans plus a ``match_level`` field:
    - "exact": direct intersection with GT after canonicalization
    - "alias_only": matched via true alias resolution
    - "container": matched at container level only (not counted as overall_match)
    - "miss": no meaningful relationship
    """
    if status != "ok":
        return _result(False, False, False, "miss")

    detected_mimes = set(semantic["mime_types"])
    detected_exts = set(semantic["extensions"])
    gt_mimes = set(ground_truth.mimes)
    gt_exts = set(ground_truth.extensions)

    # Extension matching: direct set intersection (extensions have no aliases).
    extension_match = bool(detected_exts & gt_exts)

    # MIME matching: three tiers.
    # Tier 1 — exact: any detected MIME directly appears in GT.
    if detected_mimes & gt_mimes:
        return _result(True, extension_match, extension_match, "exact")

    # Tier 2 — alias: canonicalize both sides and re-check.
    canon_detected = {canonical_mime(m) for m in detected_mimes}
    canon_gt = {canonical_mime(m) for m in gt_mimes}
    if canon_detected & canon_gt:
        return _result(True, extension_match, extension_match, "exact")

    # Also check reverse alias direction (GT uses alias name, backend uses canonical).
    rev_detected = {_ALIASES_REVERSE.get(m, m) for m in detected_mimes}
    if rev_detected & gt_mimes:
        return _result(True, extension_match, extension_match, "exact")

    # Tier 3 — container: backend found the parent wrapper. Informational.
    container_hit = False
    for detected in detected_mimes:
        children = CONTAINER_RELATIONS.get(detected, frozenset())
        if gt_mimes & children:
            container_hit = True
            break

    if container_hit:
        # Container match: mime_match stays False (subtype not identified),
        # overall_match stays False, but we report the level for diagnostics.
        return _result(False, extension_match, False, "container")

    return _result(False, extension_match, False, "miss")


def _result(
    mime_match: bool,
    extension_match: bool,
    overall_match: bool,
    match_level: str,
) -> dict[str, object]:
    return {
        "mime_match": mime_match,
        "extension_match": extension_match,
        "overall_match": overall_match,
        "match_level": match_level,
    }
