"""Thin psycopg connection helper. No ORM — the schema is small enough
that hand-written SQL in each module stays more readable than a mapping
layer, and it keeps query behavior (especially the pgvector similarity
search in ingest/dedupe.py) transparent.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

from kriyon_bd.settings import Settings


@contextmanager
def connect(settings: Settings) -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
