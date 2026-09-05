"""Deduplication: exact match via content_hash, near-duplicate via a
cosine-similarity search over pgvector embeddings.

Embedding strategy: Phase 1 uses a deterministic feature-hashing "embedding"
(no model download, no external API, no extra cost) as a placeholder good
enough to catch near-identical re-publications and minor text edits of the
same notice. It is NOT a semantic embedding — it won't catch true
paraphrases. If that turns out to matter once real data is flowing, swap
`embed_text` for a real embedding model (sentence-transformers, Voyage,
etc.); the pgvector column and query already support that, you'd just need
to re-embed existing rows and match EMBEDDING_DIM in settings.py.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Optional
from uuid import UUID

import psycopg
from pgvector import Vector

from kriyon_bd.settings import EMBEDDING_DIM

_TOKEN_RE = re.compile(r"[a-z0-9]+")

NEAR_DUP_COSINE_THRESHOLD = 0.92


def embed_text(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic feature-hashing vector, L2-normalized so pgvector's
    cosine distance operator behaves as expected."""
    vector = [0.0] * dim
    tokens = _TOKEN_RE.findall(text.lower())
    for token in tokens:
        digest = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        index = digest % dim
        sign = 1.0 if (digest // dim) % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def find_exact_duplicate(conn: psycopg.Connection, content_hash: str) -> Optional[UUID]:
    row = conn.execute(
        "SELECT id FROM signals WHERE content_hash = %s LIMIT 1", (content_hash,)
    ).fetchone()
    return row["id"] if row else None


def find_near_duplicate(
    conn: psycopg.Connection,
    embedding: list[float],
    threshold: float = NEAR_DUP_COSINE_THRESHOLD,
) -> Optional[UUID]:
    """pgvector's `<=>` operator returns cosine distance (1 - similarity),
    so a match requires distance <= (1 - threshold)."""
    max_distance = 1 - threshold
    # psycopg only adapts pgvector.Vector (or numpy arrays) to the `vector`
    # column type, not plain Python lists -- those adapt to a Postgres
    # array and fail against the vector <=> operator.
    vector_param = Vector(embedding)
    row = conn.execute(
        """
        SELECT id, embedding <=> %s AS distance
        FROM signals
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s
        LIMIT 1
        """,
        (vector_param, vector_param),
    ).fetchone()
    if row and row["distance"] <= max_distance:
        return row["id"]
    return None
