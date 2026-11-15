from openai import OpenAI

from knowledgehub.config import (
    EMBEDDING_DIMENSIONS,
    OPENAI_API_KEY,
    OPENAI_EMBEDDING_MODEL,
)

BATCH_SIZE = 64


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = OpenAI(api_key=OPENAI_API_KEY)
    vectors: list[list[float] | None] = [None] * len(texts)
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=batch,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        for item in response.data:
            vectors[start + item.index] = list(item.embedding)
    if any(vector is None or len(vector) != EMBEDDING_DIMENSIONS for vector in vectors):
        raise RuntimeError("embedding response was incomplete")
    return vectors
