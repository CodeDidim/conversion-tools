"""Shared constants for conversion tools."""

# File extensions treated as text for template processing
TEXT_EXTENSIONS = {
    ".py", ".robot", ".yaml", ".yml", ".md", ".txt",
    ".toml", ".sh", ".ps1", ".gitignore", ".dockerignore",
    ".in", ".example", ".validate", ".excalidraw", ".log"
}

# Common binary file extensions that should never be processed as text
BINARY_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".db", ".sqlite",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".pdf", ".zip",
    ".tar", ".gz", ".rar", ".7z", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".mp3", ".mp4", ".avi", ".mov", ".ttf", ".otf",
    ".woff", ".class", ".jar", ".pyc", ".pyo", ".o", ".a", ".lib",
}

# Add other shared constants here
KEYWORDS = [
    "YourCompany",
    "MY_ORGANIZATION_NAME",
    "@company.com",
    "embedded-test-team@",
]

