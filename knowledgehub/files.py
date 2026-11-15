from pathlib import Path
from uuid import UUID

from knowledgehub.config import ROOT, STORAGE_DIR


def save_upload(document_id: UUID, filename: str, data: bytes) -> Path:
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("filename is missing")
    directory = STORAGE_DIR / str(document_id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / safe_name
    path.write_bytes(data)
    return path


def delete_upload(path: Path) -> None:
    if path.is_file():
        path.unlink()
    parent = path.parent
    if parent != STORAGE_DIR and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()


def storage_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()
