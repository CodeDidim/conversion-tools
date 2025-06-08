import argparse
import os
import shutil
from pathlib import Path

KEYWORDS = [
    "YourCompany",
    "MY_ORGANIZATION_NAME",
    "@company.com",
    "embedded-test-team@",
]

TEXT_EXTENSIONS = {".py", ".robot", ".yaml", ".md"}


def should_filter_line(line: str) -> bool:
    """Return True if the line contains any of the keywords."""
    for kw in KEYWORDS:
        if kw in line:
            return True
    return False


def copy_and_clean_file(src: Path, dst: Path) -> None:
    """Copy ``src`` to ``dst`` removing lines with keywords for text files."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix in TEXT_EXTENSIONS:
        with src.open("r", errors="ignore") as f_src, dst.open("w") as f_dst:
            for line in f_src:
                if not should_filter_line(line):
                    f_dst.write(line)
    else:
        shutil.copy2(src, dst)


def export_directory(src_dir: Path, dst_dir: Path) -> None:
    """Walk ``src_dir`` copying files to ``dst_dir``."""
    for root, dirs, files in os.walk(src_dir):
        for name in files:
            src_path = Path(root) / name
            rel_path = src_path.relative_to(src_dir)
            dst_path = dst_dir / rel_path
            copy_and_clean_file(src_path, dst_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export directory removing private keywords")
    parser.add_argument("src", type=Path, help="Source directory")
    parser.add_argument("dst", type=Path, help="Target directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_directory(args.src, args.dst)


if __name__ == "__main__":
    main()
