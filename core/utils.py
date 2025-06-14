from __future__ import annotations
import mimetypes
import re
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


def sanitize_identifier(value: str) -> str:
    """Convert a value to a valid Python identifier.

    Args:
        value: String to sanitize

    Returns:
        Valid Python identifier

    Examples:
        >>> sanitize_identifier("ACME Corp")
        'ACME_Corp'
        >>> sanitize_identifier("123-test")
        'test'
        >>> sanitize_identifier("my-variable-name")
        'my_variable_name'
    """
    # Replace non-alphanumeric with underscore
    sanitized = re.sub(r'[^\w]', '_', value)

    # Remove leading digits
    sanitized = re.sub(r'^\d+', '', sanitized)

    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Strip underscores from ends
    sanitized = sanitized.strip('_')

    # Ensure not empty or Python keyword
    if not sanitized or sanitized in {'class', 'def', 'return', 'if', 'else', 'for', 'while', 'import', 'from'}:
        sanitized = f'var_{sanitized}' if sanitized else 'unnamed'

    return sanitized


def is_valid_identifier(name: str) -> bool:
    """Check if a string is a valid Python identifier."""
    import keyword
    return name.isidentifier() and not keyword.iskeyword(name)
