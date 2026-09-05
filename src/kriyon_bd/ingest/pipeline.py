"""Orchestrates one TED ingestion run: fetch -> parse -> dedupe -> store.
Pure orchestration, no CLI framework concerns — see cli.py for the command.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

import psycopg
from pgvector import Vector
from psycopg.types.json import Jsonb

from kriyon_bd.ingest.dedupe import embed_text, find_exact_duplicate, find_near_duplicate
from kriyon_bd.ingest.ted_client import TedClient, TedSourceConfig
from kriyon_bd.ingest.ted_parser import parse_contact_point, parse_notice
from kriyon_bd.logging_conf import get_logger
from kriyon_bd.models import ContactPoint, Signal

logger = get_logger(__name__)


def run_ted_ingest(
    conn: psycopg.Connection, base_url: str, since: Optional[date] = None
) -> dict[str, int]:
    config = TedSourceConfig.load()
    counts = {
        "fetched": 0,
        "inserted": 0,
        "exact_duplicate": 0,
        "near_duplicate": 0,
        "contacts_inserted": 0,
    }

    with TedClient(base_url=base_url) as client:
        for raw in client.search(config, since=since):
            counts["fetched"] += 1
            signal = parse_notice(raw)

            if find_exact_duplicate(conn, signal.content_hash):
                counts["exact_duplicate"] += 1
                continue

            embedding_text = f"{signal.title} {signal.buyer_name or ''} {' '.join(signal.cpv_codes)}"
            embedding = embed_text(embedding_text)
            near_dup_id = find_near_duplicate(conn, embedding)
            if near_dup_id:
                counts["near_duplicate"] += 1
                logger.info(
                    "ted_near_duplicate_skipped",
                    source_id=signal.source_id,
                    matched_signal_id=str(near_dup_id),
                )
                continue

            signal.embedding = embedding
            signal_id = _insert_signal(conn, signal)
            counts["inserted"] += 1

            contact = parse_contact_point(raw, signal)
            if contact:
                contact.signal_id = signal_id
                _insert_contact(conn, contact)
                counts["contacts_inserted"] += 1

    logger.info("ted_ingest_complete", **counts)
    return counts


def _insert_signal(conn: psycopg.Connection, signal: Signal) -> UUID:
    row = conn.execute(
        """
        INSERT INTO signals (
            source, source_id, source_url, title, summary, raw_payload,
            cpv_codes, country, buyer_name, publication_date, deadline_date,
            content_hash, embedding, retrieved_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            signal.source,
            signal.source_id,
            signal.source_url,
            signal.title,
            signal.summary,
            Jsonb(signal.raw_payload),
            signal.cpv_codes,
            signal.country,
            signal.buyer_name,
            signal.publication_date,
            signal.deadline_date,
            signal.content_hash,
            Vector(signal.embedding) if signal.embedding is not None else None,
            signal.retrieved_at,
        ),
    ).fetchone()
    return row["id"]


def _insert_contact(conn: psycopg.Connection, contact: ContactPoint) -> None:
    conn.execute(
        """
        INSERT INTO contacts (
            signal_id, organisation_id, name, role, email, phone,
            source_url, retrieved_at, legitimate_interest_basis
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            contact.signal_id,
            contact.organisation_id,
            contact.name,
            contact.role,
            contact.email,
            contact.phone,
            contact.source_url,
            contact.retrieved_at,
            contact.legitimate_interest_basis,
        ),
    )
