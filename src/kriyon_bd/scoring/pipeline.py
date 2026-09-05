"""Orchestrates scoring: pull unscored signals, classify, store results."""

from __future__ import annotations

from typing import Optional

import psycopg
from psycopg.types.json import Jsonb

from kriyon_bd.logging_conf import get_logger
from kriyon_bd.models import Signal, SignalScore
from kriyon_bd.scoring.classifier import SignalClassifier

logger = get_logger(__name__)


def fetch_unscored_signals(conn: psycopg.Connection, limit: Optional[int] = None) -> list[Signal]:
    query = """
        SELECT s.* FROM signals s
        LEFT JOIN signal_scores sc ON sc.signal_id = s.id
        WHERE sc.id IS NULL
        ORDER BY s.publication_date DESC NULLS LAST
    """
    if limit:
        rows = conn.execute(query + " LIMIT %s", (limit,)).fetchall()
    else:
        rows = conn.execute(query).fetchall()
    return [_row_to_signal(row) for row in rows]


def _row_to_signal(row: dict) -> Signal:
    return Signal(
        id=row["id"],
        source=row["source"],
        source_id=row["source_id"],
        source_url=row["source_url"],
        title=row["title"],
        summary=row["summary"],
        raw_payload=row["raw_payload"],
        cpv_codes=row["cpv_codes"] or [],
        country=row["country"],
        buyer_name=row["buyer_name"],
        publication_date=row["publication_date"],
        deadline_date=row["deadline_date"],
        content_hash=row["content_hash"],
        retrieved_at=row["retrieved_at"],
        organisation_id=row["organisation_id"],
    )


def store_score(conn: psycopg.Connection, score: SignalScore) -> None:
    conn.execute(
        """
        INSERT INTO signal_scores (
            signal_id, rubric_version,
            fit_score, fit_justification,
            timing_score, timing_justification,
            reachability_score, reachability_justification,
            evidence_score, evidence_justification,
            total_score, surfaced, model_name, raw_model_response
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            score.signal_id,
            score.rubric_version,
            score.fit.score,
            score.fit.justification,
            score.timing.score,
            score.timing.justification,
            score.reachability.score,
            score.reachability.justification,
            score.evidence_quality.score,
            score.evidence_quality.justification,
            score.total_score,
            score.surfaced,
            score.model_name,
            Jsonb(score.raw_model_response),
        ),
    )


def run_scoring(
    conn: psycopg.Connection, classifier: SignalClassifier, limit: Optional[int] = None
) -> dict[str, int]:
    signals = fetch_unscored_signals(conn, limit=limit)
    counts = {"scored": 0, "surfaced": 0}
    for signal in signals:
        score = classifier.score(signal)
        store_score(conn, score)
        counts["scored"] += 1
        if score.surfaced:
            counts["surfaced"] += 1
    logger.info("scoring_complete", **counts)
    return counts
