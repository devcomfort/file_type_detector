"""Typed records for reviewed backend-conformance inventory data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class FixtureReference:
    """A fixture path and the digest that identifies its reviewed bytes."""

    path: str
    sha256: str


@dataclass(frozen=True)
class GroundTruth:
    """The MIME types and extensions established by review evidence."""

    mimes: tuple[str, ...]
    extensions: tuple[str, ...]


@dataclass(frozen=True)
class GroundTruthReview:
    """The review state and supporting evidence for one candidate."""

    status: str
    reviewed_by: str | None
    reviewed_at: str | None
    evidence: tuple[str, ...]
    reason: str | None


@dataclass(frozen=True)
class SourceIntegrity:
    """Provenance of the fixture bytes (truth axis 1).

    ``external`` records carry an immutable upstream URL + commit and a
    verified git blob SHA. ``generated`` records carry the generator symbol
    and a recipe hash, plus which gate tier applies.
    """

    kind: str  # "external" | "generated"
    origin_url: str | None = None
    origin_commit: str | None = None
    blob_sha1_verified: bool | None = None
    generator_symbol: str | None = None
    recipe_hash: str | None = None
    tier: str | None = None  # "exact-byte" | "pinned-sha-roundtrip"


@dataclass(frozen=True)
class FormatValidity:
    """Independent structural validation of the fixture (truth axis 2)."""

    status: str  # "verified" | "needs_review" | "failed"
    validator: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundTruthEvidence:
    """Structured authority mapping for each GT claim (truth axis 3).

    Every claimed MIME type must carry an authority name and reference;
    extensions inherit the MIME evidence or carry an explicit note.
    """

    mime_claims: tuple[Mapping[str, str], ...]
    extension_claims: tuple[Mapping[str, str], ...] = ()


_IDENTIFIABILITY_TIERS = frozenset(
    {"distinctive", "ambiguous", "generic-container", "not_applicable"}
)


@dataclass(frozen=True)
class InventoryRecord:
    """One reviewed candidate or authoritative conformance fixture."""

    id: str
    fixture: FixtureReference
    probe_extension: str
    ground_truth: GroundTruth
    provenance: str
    ground_truth_review: GroundTruthReview
    backends: tuple[str, ...]
    source_integrity: SourceIntegrity | None = None
    format_validity: FormatValidity | None = None
    ground_truth_evidence: GroundTruthEvidence | None = None
    content_identifiability: str | None = None

    def __post_init__(self) -> None:
        if (
            self.content_identifiability is not None
            and self.content_identifiability not in _IDENTIFIABILITY_TIERS
        ):
            raise ValueError(
                f"{self.id}: unsupported content_identifiability tier "
                f"{self.content_identifiability!r}"
            )
