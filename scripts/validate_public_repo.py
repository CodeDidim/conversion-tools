import re
import sys
from pathlib import Path
from typing import Iterable, Tuple, List, Pattern


COMPANY_PATTERNS = [
    r"YourCompany",
    r"MY_ORGANIZATION_NAME",
    r"@company\.com",
    r"embedded-test-team@",
]

EMAIL_PATTERN = r"[\w.-]+@[\w.-]+"
IP_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
TOKEN_PATTERNS = [
    r"token\s+[\w-]+",
    r"api[_-]?key\s*=\s*\S+",
    r"secret\s*=\s*\S+",
    r"password\s*[=:]\s*\S+",
    r"aws_secret_access_key\s*=\s*\S+",
    r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----",
    r"ssh-rsa\s+[A-Za-z0-9+/]+",
]


def build_patterns() -> Iterable[Tuple[Pattern, str]]:
    patterns: List[Tuple[Pattern, str]] = []
    patterns.extend((re.compile(p, re.IGNORECASE), "Company reference") for p in COMPANY_PATTERNS)
    patterns.append((re.compile(EMAIL_PATTERN, re.IGNORECASE), "Email"))
    patterns.append((re.compile(IP_PATTERN), "IP address"))
    patterns.extend((re.compile(p, re.IGNORECASE), "Token") for p in TOKEN_PATTERNS)
    return patterns


PATTERNS = list(build_patterns())


def scan_file(path: Path) -> bool:
    """Return True if no sensitive patterns found in file."""
    ok = True
    with path.open("r", errors="ignore") as f:
        for lineno, line in enumerate(f, start=1):
            for regex, desc in PATTERNS:
                if regex.search(line):
                    print(f"{path}:{lineno}: {desc} -> {line.strip()}")
                    ok = False
    return ok


def validate_directory(base_dir: Path) -> bool:
    """Scan all files under ``base_dir`` and report sensitive data."""
    ok = True
    for file in base_dir.rglob("*"):
        if file.is_file():
            if not scan_file(file):
                ok = False
    return ok


def main() -> None:
    base = Path("clean_export")
    success = validate_directory(base)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
