from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from knowledgehub.chunk import chunk_text
from knowledgehub.db import connect, insert_chunk, insert_document
from knowledgehub.embed import embed_texts
from knowledgehub.extract import DOCX, MARKDOWN, PDF, TEXT, extract_pages
from knowledgehub.files import delete_upload, save_upload, storage_path

MEDIA_TYPES = {
    ".pdf": PDF,
    ".docx": DOCX,
    ".md": MARKDOWN,
    ".markdown": MARKDOWN,
    ".txt": TEXT,
}


def upload_document(filename: str, data: bytes) -> dict:
    safe_name = Path(filename).name
    media_type = MEDIA_TYPES.get(Path(safe_name).suffix.lower())
    if media_type is None:
        raise ValueError("unsupported file type")

    document_id = uuid4()
    path = save_upload(document_id, safe_name, data)
    try:
        chunks = chunk_text(extract_pages(path, media_type))
        if not chunks:
            raise ValueError("document has no text")
        vectors = embed_texts([chunk.text for chunk in chunks])
        with connect() as connection:
            insert_document(
                connection,
                document_id,
                safe_name,
                media_type,
                storage_path(path),
                datetime.now(timezone.utc),
            )
            for chunk, vector in zip(chunks, vectors, strict=True):
                insert_chunk(
                    connection,
                    uuid4(),
                    document_id,
                    chunk.ordinal,
                    chunk.text,
                    chunk.page,
                    vector,
                )
    except Exception:
        delete_upload(path)
        raise
    return {
        "id": str(document_id),
        "filename": safe_name,
        "chunk_count": len(chunks),
    }
