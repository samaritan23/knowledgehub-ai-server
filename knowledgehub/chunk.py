from dataclasses import dataclass

from knowledgehub.config import CHUNK_WORDS, OVERLAP_WORDS


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    text: str
    page: int


def chunk_text(pages: list[dict]) -> list[Chunk]:
    if OVERLAP_WORDS >= CHUNK_WORDS:
        raise RuntimeError("OVERLAP_WORDS must be smaller than CHUNK_WORDS")

    words: list[tuple[int, str]] = []
    for page in pages:
        for word in str(page["text"]).split():
            words.append((int(page["page"]), word))
    if not words:
        return []

    chunks: list[Chunk] = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))
        piece = words[start:end]
        chunks.append(
            Chunk(
                ordinal=len(chunks),
                text=" ".join(word for _, word in piece),
                page=piece[0][0],
            )
        )
        if end == len(words):
            break
        next_start = end - OVERLAP_WORDS
        if next_start <= start:
            break
        start = next_start
    return chunks
