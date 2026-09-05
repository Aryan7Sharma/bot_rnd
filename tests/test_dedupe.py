from kriyon_bd.ingest.dedupe import embed_text
from kriyon_bd.settings import EMBEDDING_DIM


def test_embed_text_is_deterministic():
    a = embed_text("Terminal operating system upgrade")
    b = embed_text("Terminal operating system upgrade")
    assert a == b


def test_embed_text_has_configured_dimension():
    vector = embed_text("anything")
    assert len(vector) == EMBEDDING_DIM


def test_embed_text_is_l2_normalized():
    vector = embed_text("Hamburg Port Authority terminal upgrade")
    norm = sum(v * v for v in vector) ** 0.5
    assert abs(norm - 1.0) < 1e-9


def test_embed_text_empty_string_is_zero_vector():
    vector = embed_text("")
    assert all(v == 0.0 for v in vector)


def test_similar_titles_are_closer_than_unrelated_ones():
    a = embed_text("Terminal operating system migration for container terminal")
    b = embed_text("Terminal operating system migration for container terminal, phase 2")
    c = embed_text("Catering services framework agreement for staff canteen")

    def cosine(x, y):
        return sum(xi * yi for xi, yi in zip(x, y))

    assert cosine(a, b) > cosine(a, c)
