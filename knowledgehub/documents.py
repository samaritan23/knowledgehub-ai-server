from pathlib import Path
from uuid import UUID

from psycopg.rows import dict_row

from knowledgehub.config import ROOT, STORAGE_DIR
from knowledgehub.db import connect, execute
from knowledgehub.files import delete_upload


def list_documents() -> list[dict]:
    with connect() as connection:
        connection.row_factory = dict_row
        rows = execute(
            connection,
            """
            SELECT id::text AS id, filename, created_at
            FROM documents
            ORDER BY created_at DESC
            """,
        ).fetchall()
    return [
        {
            "id": row["id"],
            "filename": row["filename"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]


def delete_document(document_id: str) -> None:
    try:
        parsed_id = UUID(document_id)
    except ValueError as error:
        raise ValueError("document id is invalid") from error

    with connect() as connection:
        connection.row_factory = dict_row
        row = execute(
            connection,
            "SELECT storage_path FROM documents WHERE id = %s",
            (parsed_id,),
        ).fetchone()
        if row is None:
            raise LookupError("document not found")
        path = _stored_file(row["storage_path"])
        execute(connection, "DELETE FROM documents WHERE id = %s", (parsed_id,))
        delete_upload(path)


def _stored_file(storage_path: str) -> Path:
    path = (ROOT / storage_path).resolve()
    storage_root = STORAGE_DIR.resolve()
    if not path.is_relative_to(storage_root):
        raise ValueError("document path is invalid")
    return path
