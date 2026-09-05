"""GDPR deletion path: purge all data for a given contact or organisation,
logging what was removed. This exists from day one per the project's hard
constraint — no soft-delete flag, no "add it later."

Design choice worth flagging: purging an organisation deletes its
`contacts` (the personal data) and the `organisations` row itself, but
only unlinks (does not delete) the `signals` referencing it. A TED notice
is a public procurement record, not personal data about the buyer, so
GDPR's deletion right doesn't reach it — but confirm this reading matches
your intent before relying on it for a real request.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb


def purge_contact(
    conn: psycopg.Connection,
    contact_id: Optional[UUID] = None,
    email: Optional[str] = None,
    reason: str = "",
) -> dict[str, int]:
    if not contact_id and not email:
        raise ValueError("purge_contact requires contact_id or email")

    if contact_id:
        rows = conn.execute(
            "DELETE FROM contacts WHERE id = %s RETURNING id", (contact_id,)
        ).fetchall()
        target_id = contact_id
    else:
        rows = conn.execute(
            "DELETE FROM contacts WHERE email = %s RETURNING id", (email,)
        ).fetchall()
        target_id = rows[0]["id"] if rows else None

    counts = {"contacts": len(rows)}
    if target_id:
        _log_deletion(conn, "contact", target_id, reason, counts)
    return counts


def purge_organisation(
    conn: psycopg.Connection, organisation_id: UUID, reason: str = ""
) -> dict[str, int]:
    contact_rows = conn.execute(
        "DELETE FROM contacts WHERE organisation_id = %s RETURNING id", (organisation_id,)
    ).fetchall()
    signal_rows = conn.execute(
        "UPDATE signals SET organisation_id = NULL WHERE organisation_id = %s RETURNING id",
        (organisation_id,),
    ).fetchall()
    org_rows = conn.execute(
        "DELETE FROM organisations WHERE id = %s RETURNING id", (organisation_id,)
    ).fetchall()

    counts = {
        "contacts": len(contact_rows),
        "signals_unlinked": len(signal_rows),
        "organisations": len(org_rows),
    }
    _log_deletion(conn, "organisation", organisation_id, reason, counts)
    return counts


def _log_deletion(
    conn: psycopg.Connection,
    target_type: str,
    target_id: UUID,
    reason: str,
    counts: dict[str, int],
) -> None:
    conn.execute(
        """
        INSERT INTO deletion_log (target_type, target_id, reason, deleted_counts)
        VALUES (%s, %s, %s, %s)
        """,
        (target_type, target_id, reason or None, Jsonb(counts)),
    )
