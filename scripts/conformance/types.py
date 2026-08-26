"""Typed records for reviewed backend-conformance inventory data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class FixtureReference:
    path: str
    sha256: str


@dataclass(frozen=True)
class GroundTruth:
    mimes: tuple[str, ...]
    extensions: tuple[str, ...]


@dataclass(frozen=True)
class GroundTruthReview:
    status: str
    reviewed_by: str | None
    reviewed_at: str | None
    evidence: tuple[str, ...]
    reason: str | None


@dataclass(frozen=True)
class SourceIntegrity:
    kind: str
    origin_url: str | None = None
    origin_commit: str | None = None
    blob_sha1_verified: bool | None = None
    generator_symbol: str | None = None
    recipe_hash: str | None = None
    tier: str | None = None


@dataclass(frozen=True)
class FormatValidity:
    status: str
    validator: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundTruthEvidence:
    mime_claims: tuple[Mapping[str, str], ...]
    extension_claims: tuple[Mapping[str, str], ...] = ()


_IDENTIFIABILITY_TIERS = frozenset(
    {"distinctive", "ambiguous", "generic-container", "not_applicable"}
)


@dataclass(frozen=True)
class InventoryRecord:
    id: str
    fixture: FixtureReference
    ground_truth: GroundTruth
    provenance: str
    ground_truth_review: GroundTruthReview
    backends: tuple[str, ...]
    probe_extension: str | None = None
    probe_filename: str | None = None
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
        if not self.probe_extension and not self.probe_filename:
            raise ValueError(
                f"{self.id}: exactly one of probe_extension or "
                "probe_filename must be set"
            )
