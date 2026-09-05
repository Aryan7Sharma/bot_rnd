"""Deterministic parsing of raw TED API notices into normalized Signal /
ContactPoint objects. No model calls here — see scoring/classifier.py for
where the LLM boundary starts.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from typing import Any, Optional

from kriyon_bd.models import ContactPoint, Signal

TED_NOTICE_URL_TEMPLATE = "https://ted.europa.eu/en/notice/-/detail/{publication_number}"


def _pick_text(value: Any, preferred_langs: tuple[str, ...] = ("eng", "deu")) -> str:
    """TED multilingual fields come back as {"eng": "...", "deu": "..."}.
    Pick a preferred language, falling back to whatever is present."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for lang in preferred_langs:
            text = value.get(lang)
            if text:
                return text
        for text in value.values():
            if text:
                return text
    return ""


def _parse_date(value: Any) -> Optional[date]:
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _content_hash(publication_number: str, title: str, buyer_name: str) -> str:
    key = f"{publication_number}|{title}|{buyer_name}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def _extract_source_url(raw: dict[str, Any], publication_number: str) -> str:
    links = raw.get("links")
    if isinstance(links, dict):
        for key in ("html", "pdf", "xml"):
            candidate = links.get(key)
            if isinstance(candidate, dict):
                candidate = candidate.get("eng") or next(iter(candidate.values()), None)
            if candidate:
                return candidate
    return TED_NOTICE_URL_TEMPLATE.format(publication_number=publication_number)


def parse_notice(raw: dict[str, Any], retrieved_at: Optional[datetime] = None) -> Signal:
    retrieved_at = retrieved_at or datetime.now(timezone.utc)

    publication_number = str(raw.get("publication-number", "")).strip()
    title = _pick_text(raw.get("notice-title"))
    buyer_name = _pick_text(raw.get("buyer-name"))
    country = raw.get("buyer-country")
    cpv = raw.get("classification-cpv") or []
    if isinstance(cpv, str):
        cpv = [cpv]

    publication_date = _parse_date(raw.get("publication-date"))
    deadline_date = _parse_date(raw.get("deadline-receipt-request") or raw.get("deadline"))
    source_url = _extract_source_url(raw, publication_number)

    summary_parts = [p for p in [title, f"Buyer: {buyer_name}" if buyer_name else None] if p]
    summary = ". ".join(summary_parts) or title or "(no title in source notice)"

    return Signal(
        source="ted",
        source_id=publication_number,
        source_url=source_url,
        title=title or "(untitled TED notice)",
        summary=summary,
        raw_payload=raw,
        cpv_codes=[str(c) for c in cpv],
        country=country,
        publication_date=publication_date,
        deadline_date=deadline_date,
        content_hash=_content_hash(publication_number, title, buyer_name),
        retrieved_at=retrieved_at,
        buyer_name=buyer_name or None,
    )


def parse_contact_point(
    raw: dict[str, Any], signal: Signal, retrieved_at: Optional[datetime] = None
) -> Optional[ContactPoint]:
    """Extract a named contact from the notice's contact-point field, if
    present. Returns None rather than a ContactPoint with placeholder
    provenance — GDPR provenance is mandatory, not best-effort, so a
    contact with no source data simply isn't recorded.
    """
    contact_raw = raw.get("contact-point")
    if isinstance(contact_raw, list):
        contact_raw = contact_raw[0] if contact_raw else None
    if not isinstance(contact_raw, dict):
        return None

    name = _pick_text(contact_raw.get("name")) or None
    email = contact_raw.get("email") or None
    phone = contact_raw.get("phone") or None
    role = _pick_text(contact_raw.get("role")) or None

    if not any([name, email, phone]):
        return None

    return ContactPoint(
        name=name,
        role=role,
        email=email,
        phone=phone,
        source_url=signal.source_url,
        retrieved_at=retrieved_at or signal.retrieved_at,
        legitimate_interest_basis=(
            "Published by the contracting authority as the designated point of "
            "contact for this public tender notice; disclosed by the buyer for "
            "the purpose of receiving tender queries and submissions "
            "(GDPR Art. 6(1)(f), legitimate interest in professional B2G contact)."
        ),
        signal_id=signal.id,
    )
