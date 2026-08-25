"""Normalize MIME aliases and compare detector output to reviewed Ground Truth.

Four match levels are reported:
- exact: detected MIME directly equals a GT entry
- alias: detected MIME is a documented true alias of a GT entry (bidirectional,
  per shared-mime-info <alias> or IANA rename); counts toward overall_match
- subtype: detected MIME is a documented subclass of the GT parent
  (shared-mime-info <sub-class-of>); counts toward overall_match
- container: detected MIME is the generic container of the GT format
  (informational only; does NOT count toward overall_match)

Hierarchy relationships are directional:
- detected child → GT parent: subtype (PASS)
- detected parent → GT child: container (partial, NOT overall_match)
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from scripts.conformance.types import GroundTruth

# True MIME aliases: bidirectional equivalence, backed by shared-mime-info
# <alias> elements or IANA renames. Both names refer to the exact same type.
MIME_ALIASES: dict[str, str] = {
    "application/x-debian-package": "application/vnd.debian.binary-package",
    "text/x-markdown": "text/markdown",
}

# Reverse map for lookup convenience.
_ALIASES_REVERSE: dict[str, str] = {v: k for k, v in MIME_ALIASES.items()}

# Subclass hierarchy (directional): child → parent.
# Backed by shared-mime-info <sub-class-of> or vendor documentation.
# If the backend detects the child and GT says the parent, that's a subtype match
# (more specific than required → PASS).
# If the backend detects the parent and GT says the child, that's a container
# match (less specific → informational only, NOT overall_match).
SUBCLASS_OF: dict[str, str] = {
    # shared-mime-info defines application/x-x509-ca-cert as sub-class-of application/pkix-cert
    "application/x-x509-ca-cert": "application/pkix-cert",
}

# Reverse: parent → set of known children.
_CHILDREN_OF: dict[str, set[str]] = {}
for _child, _parent in SUBCLASS_OF.items():
    _CHILDREN_OF.setdefault(_parent, set()).add(_child)

# Container relationships: parent container MIME -> set of child formats it can hold.
CONTAINER_RELATIONS: dict[str, frozenset[str]] = {
    "application/zip": frozenset(
        {
            "application/vnd.android.package-archive",
            "application/java-archive",
            "application/epub+zip",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    ),
}


def canonical_mime(mime_type: str) -> str:
    """Return the canonical form of a MIME type by resolving true aliases."""
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

    Returns match booleans plus ``match_level``:
    - "exact": direct intersection
    - "alias": true alias resolution (bidirectional)
    - "subtype": backend found a more specific type than GT requires (PASS)
    - "container": backend found only the generic wrapper (NOT overall_match)
    - "miss": no relationship
    """
    if status != "ok":
        return _result(False, False, False, "miss")

    detected_mimes = set(semantic["mime_types"])
    detected_exts = set(semantic["extensions"])
    gt_mimes = set(ground_truth.mimes)
    gt_exts = set(ground_truth.extensions)

    extension_match = bool(detected_exts & gt_exts)

    # Tier 1 — exact: direct intersection.
    if detected_mimes & gt_mimes:
        return _result(True, extension_match, extension_match, "exact")

    # Tier 2 — alias: bidirectional true-alias resolution.
    canon_detected = {canonical_mime(m) for m in detected_mimes}
    canon_gt = {canonical_mime(m) for m in gt_mimes}
    if canon_detected & canon_gt:
        return _result(True, extension_match, extension_match, "alias")

    rev_detected = {_ALIASES_REVERSE.get(m, m) for m in detected_mimes}
    if rev_detected & gt_mimes:
        return _result(True, extension_match, extension_match, "alias")

    # Tier 3 — subtype: backend detected a MORE specific type than GT requires.
    # Direction: detected child whose parent is in GT → PASS.
    for detected in detected_mimes:
        parent = SUBCLASS_OF.get(detected)
        if parent and parent in gt_mimes:
            return _result(True, extension_match, extension_match, "subtype")

    # Tier 4 — container: backend detected only the generic wrapper.
    # Direction: detected parent whose children include a GT entry → partial.
    for detected in detected_mimes:
        children = _CHILDREN_OF.get(detected, set())
        if gt_mimes & children:
            return _result(False, extension_match, False, "container")

        # Also check CONTAINER_RELATIONS (non-subclass containment)
        related = CONTAINER_RELATIONS.get(detected, frozenset())
        if gt_mimes & related:
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
