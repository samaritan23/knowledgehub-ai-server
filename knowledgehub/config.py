import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _required(name: str) -> str:
    value = _env(name)
    if not value:
        raise RuntimeError(f"Missing {name}")
    return value


DATABASE_URL = _required("DATABASE_URL")
OPENAI_API_KEY = _required("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = _env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_CHAT_MODEL = _env("OPENAI_CHAT_MODEL", "gpt-4.1-mini")

STORAGE_DIR = ROOT / "storage"

CHUNK_WORDS = 400
OVERLAP_WORDS = 50
EMBEDDING_DIMENSIONS = 1536

VECTOR_TOP_K = 20
KEYWORD_TOP_K = 20
RESULT_TOP_K = 5
RRF_K = 60
MIN_COSINE_SIMILARITY = 0.25
MAX_KEYWORD_RANK = 10
