import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql

from knowledgehub.config import DATABASE_URL, EMBEDDING_DIMENSIONS

STATIC_STATEMENTS = (
    "CREATE EXTENSION IF NOT EXISTS vector",
    """
    CREATE TABLE IF NOT EXISTS documents (
        id uuid PRIMARY KEY,
        filename text NOT NULL,
        media_type text NOT NULL,
        storage_path text NOT NULL,
        created_at timestamptz NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops)
    """,
    """
    CREATE INDEX IF NOT EXISTS chunks_tsv_idx
    ON chunks USING gin (tsv)
    """,
)


def connect() -> psycopg.Connection:
    connection = psycopg.connect(DATABASE_URL)
    register_vector(connection)
    return connection


def execute(
    connection: psycopg.Connection,
    statement: str | sql.Composed,
    params: tuple = (),
):
    """Run one SQL statement. Values belong in params, never inside statement."""
    return connection.execute(statement, params)


def _chunks_table() -> sql.Composed:
    if not isinstance(EMBEDDING_DIMENSIONS, int) or EMBEDDING_DIMENSIONS < 1:
        raise RuntimeError("EMBEDDING_DIMENSIONS must be a positive integer")
    return sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id uuid PRIMARY KEY,
            document_id uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
            ordinal int NOT NULL,
            text text NOT NULL,
            page int,
            embedding vector({dimensions}) NOT NULL,
            tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
            UNIQUE (document_id, ordinal)
        )
        """
    ).format(dimensions=sql.Literal(EMBEDDING_DIMENSIONS))


def init_db() -> None:
    with connect() as connection:
        execute(connection, STATIC_STATEMENTS[0])
        execute(connection, STATIC_STATEMENTS[1])
        execute(connection, _chunks_table())
        execute(connection, STATIC_STATEMENTS[2])
        execute(connection, STATIC_STATEMENTS[3])


if __name__ == "__main__":
    init_db()
