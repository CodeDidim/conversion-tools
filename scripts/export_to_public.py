import argparse
import os
import shutil
import sys
from pathlib import Path

# Ensure this script works when executed directly from the ``scripts`` folder.
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.apply_template_context import get_log_file, write_log
from core.constants import KEYWORDS, TEXT_EXTENSIONS
from core.utils import is_binary_file


def should_filter_line(line: str) -> bool:
    """Return True if the line contains any of the keywords.

    Matching is performed case-insensitively to catch variations like
    ``yourcompany`` or ``My_Organization_Name``.
    """
    lower = line.lower()
    for kw in KEYWORDS:
        if kw.lower() in lower:
            return True
    return False


def copy_and_clean_file(src: Path, dst: Path, log_file: Path, verbose: bool) -> None:
    """Copy ``src`` to ``dst`` removing lines with keywords for text files."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if is_binary_file(src):
        write_log(f"Skipping binary file {src}", log_file, verbose)
        shutil.copy2(src, dst)
        return
    if src.suffix in TEXT_EXTENSIONS:
        with src.open("r", errors="ignore") as f_src, dst.open("w") as f_dst:
            for lineno, line in enumerate(f_src, start=1):
                if not should_filter_line(line):
                    f_dst.write(line)
                else:
                    write_log(f"{src}:{lineno} removed line", log_file, verbose)
    else:
        shutil.copy2(src, dst)


def export_directory(
    src_dir: Path,
    dst_dir: Path,
    log_file: Path = Path(os.devnull),
    verbose: bool = False,
) -> None:
    """Walk ``src_dir`` copying files to ``dst_dir``."""
    for root, dirs, files in os.walk(src_dir):
        for name in files:
            src_path = Path(root) / name
            rel_path = src_path.relative_to(src_dir)
            dst_path = dst_dir / rel_path
            copy_and_clean_file(src_path, dst_path, log_file, verbose)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export directory removing private keywords")
    parser.add_argument("src", type=Path, help="Source directory")
    parser.add_argument("dst", type=Path, help="Target directory")
    parser.add_argument("--verbose", action="store_true", help="Print log to stdout")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_file = get_log_file("export")
    export_directory(args.src, args.dst, log_file, args.verbose)


if __name__ == "__main__":
    main()
