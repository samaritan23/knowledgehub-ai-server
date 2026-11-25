from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class Usage:
    embedding_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


_current: ContextVar[Usage | None] = ContextVar("knowledgehub_usage", default=None)


def begin() -> Usage:
    usage = Usage()
    _current.set(usage)
    return usage


def add_embedding_tokens(count: int) -> None:
    usage = _current.get()
    if usage is not None:
        usage.embedding_tokens += count


def add_chat_tokens(prompt_tokens: int, completion_tokens: int) -> None:
    usage = _current.get()
    if usage is not None:
        usage.prompt_tokens += prompt_tokens
        usage.completion_tokens += completion_tokens
