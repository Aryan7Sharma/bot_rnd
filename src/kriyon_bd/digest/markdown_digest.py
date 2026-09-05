"""Renders the daily digest: top-N surfaced signals from the most recent
scoring run, as Markdown written to disk.

Phase 1 scope note: this digest intentionally does NOT include a company
dossier, "why now" narrative, Kriyon capability mapping, drafted opener,
or confidence note — those require enrichment (company research), which
is out of scope until Phase 3. See README.md for why.
"""

from __future__ import annotations

from datetime import date as date_type
from pathlib import Path
from typing import Any, Optional

import psycopg

TOP_N = 5


def fetch_top_signals(conn: psycopg.Connection, limit: int = TOP_N) -> list[dict[str, Any]]:
    return conn.execute(
        """
        SELECT s.title, s.summary, s.source_url, s.buyer_name, s.country,
               s.deadline_date,
               sc.rubric_version, sc.total_score,
               sc.fit_score, sc.fit_justification,
               sc.timing_score, sc.timing_justification,
               sc.reachability_score, sc.reachability_justification,
               sc.evidence_score, sc.evidence_justification
        FROM signal_scores sc
        JOIN signals s ON s.id = sc.signal_id
        WHERE sc.surfaced = true
        ORDER BY sc.scored_at DESC, sc.total_score DESC
        LIMIT %s
        """,
        (limit,),
    ).fetchall()


def render_digest(rows: list[dict[str, Any]], digest_date: date_type) -> str:
    lines = [
        f"# Kriyon BD Signal Digest — {digest_date.isoformat()}",
        "",
        f"{len(rows)} signal(s) surfaced."
        if rows
        else "No signals cleared the surfacing threshold today.",
        "",
    ]
    for i, row in enumerate(rows, start=1):
        lines += [
            f"## {i}. {row['title']} (score: {row['total_score']}/20, rubric {row['rubric_version']})",
            "",
            f"**Buyer:** {row['buyer_name'] or 'unknown'} | "
            f"**Country:** {row['country'] or 'unknown'} | "
            f"**Deadline:** {row['deadline_date'] or 'none listed'}",
            f"**Source:** {row['source_url']}",
            "",
            row["summary"],
            "",
            "| Axis | Score | Justification |",
            "|---|---|---|",
            f"| Fit | {row['fit_score']} | {row['fit_justification']} |",
            f"| Timing | {row['timing_score']} | {row['timing_justification']} |",
            f"| Reachability | {row['reachability_score']} | {row['reachability_justification']} |",
            f"| Evidence quality | {row['evidence_score']} | {row['evidence_justification']} |",
            "",
            '_Phase 1 digest: no company dossier, "why now" narrative, or drafted '
            "opener yet — those need enrichment, deferred to Phase 3._",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def write_digest(
    conn: psycopg.Connection, output_dir: Path, digest_date: Optional[date_type] = None
) -> Path:
    digest_date = digest_date or date_type.today()
    rows = fetch_top_signals(conn)
    content = render_digest(rows, digest_date)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{digest_date.isoformat()}.md"
    path.write_text(content)
    return path
