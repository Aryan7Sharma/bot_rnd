"""Dataclasses for the Phase 1 domain objects. No ORM (see db.py) — these
are plain data carriers between ingest -> scoring -> digest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID


@dataclass
class Organisation:
    name: str
    normalized_name: str
    country: Optional[str] = None
    org_type: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[UUID] = None


@dataclass
class Signal:
    """A normalized procurement notice, ready for storage/scoring.

    `raw_payload` keeps the full original API response for audit — every
    claim surfaced later must trace back to something in here, per the
    project's "no fabricated facts" constraint.
    """

    source: str
    source_id: str
    source_url: str
    title: str
    summary: str
    raw_payload: dict[str, Any]
    cpv_codes: list[str]
    country: Optional[str]
    publication_date: Optional[date]
    deadline_date: Optional[date]
    content_hash: str
    retrieved_at: datetime
    buyer_name: Optional[str] = None
    id: Optional[UUID] = None
    organisation_id: Optional[UUID] = None
    embedding: Optional[list[float]] = None


@dataclass
class ContactPoint:
    """A named contact extracted from a signal's source document. Every
    GDPR-provenance field is mandatory (no default), so there is no code
    path that can construct one without source_url / retrieved_at /
    legitimate_interest_basis.
    """

    name: Optional[str]
    role: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    source_url: str
    retrieved_at: datetime
    legitimate_interest_basis: str
    signal_id: Optional[UUID] = None
    organisation_id: Optional[UUID] = None
    id: Optional[UUID] = None


@dataclass
class AxisScore:
    score: int          # 0-5
    justification: str  # one sentence, required by the rubric


@dataclass
class SignalScore:
    signal_id: UUID
    rubric_version: str
    fit: AxisScore
    timing: AxisScore
    reachability: AxisScore
    evidence_quality: AxisScore
    surfaced: bool
    model_name: str
    raw_model_response: dict[str, Any]
    total_score: int = field(init=False)

    def __post_init__(self) -> None:
        self.total_score = sum(
            axis.score
            for axis in (self.fit, self.timing, self.reachability, self.evidence_quality)
        )
