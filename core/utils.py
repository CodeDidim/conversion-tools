from __future__ import annotations
import mimetypes
from pathlib import Path
from .constants import BINARY_EXTENSIONS, TEXT_EXTENSIONS


def _looks_binary(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data:
        return True
    text_chars = bytes(range(32, 127)) + b"\n\r\t\f\b"
    nontext = sum(byte not in text_chars for byte in data)
    return nontext / len(data) > 0.3


def is_binary_file(path: Path, sample_size: int = 2048) -> bool:
    """Heuristically determine if ``path`` is a binary file."""
    ext = path.suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return True

    try:
        with path.open("rb") as f:
            chunk = f.read(sample_size)
    except Exception:
        return True

    if _looks_binary(chunk):
        return True

    mtype, _ = mimetypes.guess_type(str(path))
    if mtype:
        if mtype.startswith("text"):
            return False
        if not mtype.startswith("text") and ext not in TEXT_EXTENSIONS:
            return True

    return False
