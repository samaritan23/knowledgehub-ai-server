from dataclasses import dataclass

from psycopg.rows import dict_row

from knowledgehub.config import (
    KEYWORD_TOP_K,
    MAX_KEYWORD_RANK,
    MIN_COSINE_SIMILARITY,
    RESULT_TOP_K,
    RRF_K,
    VECTOR_TOP_K,
)
from knowledgehub.db import connect, execute
from knowledgehub.embed import embed_texts

VECTOR_QUERY = """
SELECT c.id::text AS chunk_id,
       d.filename,
       c.page,
       c.text,
       1 - (c.embedding <=> %s::vector) AS cosine
FROM chunks AS c
JOIN documents AS d ON d.id = c.document_id
ORDER BY c.embedding <=> %s::vector
LIMIT %s
"""

KEYWORD_QUERY = """
SELECT c.id::text AS chunk_id,
       d.filename,
       c.page,
       c.text
FROM chunks AS c
JOIN documents AS d ON d.id = c.document_id
WHERE c.tsv @@ plainto_tsquery('english', %s)
ORDER BY ts_rank(c.tsv, plainto_tsquery('english', %s)) DESC
LIMIT %s
"""


@dataclass(frozen=True)
class Passage:
    chunk_id: str
    filename: str
    page: int | None
    text: str


@dataclass(frozen=True)
class SearchResult:
    passages: list[Passage]
    refused: bool


def search(question: str) -> SearchResult:
    embedding = embed_texts([question])[0]
    with connect() as connection:
        connection.row_factory = dict_row
        vector_rows = execute(
            connection,
            VECTOR_QUERY,
            (embedding, embedding, VECTOR_TOP_K),
        ).fetchall()
        keyword_rows = execute(
            connection,
            KEYWORD_QUERY,
            (question, question, KEYWORD_TOP_K),
        ).fetchall()

    best_cosine = float(vector_rows[0]["cosine"]) if vector_rows else None
    best_keyword_rank = 1 if keyword_rows else None
    refused = (best_cosine is None or best_cosine < MIN_COSINE_SIMILARITY) and (
        best_keyword_rank is None or best_keyword_rank > MAX_KEYWORD_RANK
    )
    if refused:
        return SearchResult(passages=[], refused=True)

    scores: dict[str, float] = {}
    passages: dict[str, Passage] = {}
    for rank, row in enumerate(vector_rows, start=1):
        chunk_id = row["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank)
        passages[chunk_id] = _passage(row)
    for rank, row in enumerate(keyword_rows, start=1):
        chunk_id = row["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (RRF_K + rank)
        passages.setdefault(chunk_id, _passage(row))

    ordered = sorted(scores, key=scores.get, reverse=True)[:RESULT_TOP_K]
    return SearchResult(
        passages=[passages[chunk_id] for chunk_id in ordered],
        refused=False,
    )


def _passage(row: dict) -> Passage:
    return Passage(
        chunk_id=row["chunk_id"],
        filename=row["filename"],
        page=row["page"],
        text=row["text"],
    )
