"""Typed records for reviewed backend-conformance inventory data."""

from __future__ import annotations

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
class InventoryRecord:
    """One reviewed candidate or authoritative conformance fixture."""

    id: str
    fixture: FixtureReference
    probe_extension: str
    ground_truth: GroundTruth
    provenance: str
    ground_truth_review: GroundTruthReview
    backends: tuple[str, ...]
