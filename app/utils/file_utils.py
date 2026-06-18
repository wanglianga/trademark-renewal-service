import os
import hashlib
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings


def ensure_upload_dir():
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def get_file_path(filename: str, subdir: str = "") -> str:
    base_path = Path(settings.UPLOAD_DIR)
    if subdir:
        base_path = base_path / subdir
    base_path.mkdir(parents=True, exist_ok=True)
    return str(base_path / filename)


def calculate_file_hash(file_content: bytes) -> str:
    return hashlib.md5(file_content).hexdigest()


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    ext = get_file_extension(filename)
    return ext in allowed_extensions


def validate_file_size(file_size: int, max_size: int = None) -> bool:
    if max_size is None:
        max_size = settings.MAX_UPLOAD_SIZE
    return file_size <= max_size


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    import uuid
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4().hex[:12])
    if prefix:
        return f"{prefix}_{unique_id}{ext}"
    return f"{unique_id}{ext}"


async def save_upload_file(file: UploadFile, subdir: str = "") -> Tuple[str, int, str]:
    ensure_upload_dir()
    file_content = await file.read()
    file_size = len(file_content)
    file_hash = calculate_file_hash(file_content)
    filename = generate_unique_filename(file.filename or "unknown")
    file_path = get_file_path(filename, subdir)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_path, file_size, file_hash
