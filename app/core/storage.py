import uuid
from pathlib import Path

from app.core.config import settings


def save_files(files: list[tuple[str, bytes]]) -> list[tuple[str, str, int]]:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for filename, content in files:
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = upload_dir / unique_name
        file_path.write_bytes(content)
        size_kb = len(content) // 1024
        saved.append((filename, str(file_path), size_kb))
    return saved
