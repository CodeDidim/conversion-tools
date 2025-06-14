import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict

# Allow running this script directly by ensuring the repository root is on
# ``sys.path`` when executed as ``python scripts/revert_template_context.py``.
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.constants import TEXT_EXTENSIONS


from scripts.apply_template_context import (
    load_profile,
    copy_project,
    get_log_file,
    write_log,
)



def replace_values_with_tokens(base_dir: Path, mapping: Dict[str, str], log_file: Path, verbose: bool) -> None:
    """Replace private values with ``{{ KEY }}`` tokens in text files."""
    # Sort keys by value length so longer strings are replaced first.
    ordered_keys = sorted(mapping, key=lambda k: len(mapping[k]), reverse=True)
    patterns = {
        key: re.compile(r"(?<!\w)" + re.escape(mapping[key]) + r"(?!\w)")
        for key in ordered_keys
    }
    for root, _, files in os.walk(base_dir):
        for name in files:
            path = Path(root) / name
            if path.suffix in TEXT_EXTENSIONS:
                text = path.read_text(encoding="utf-8")
                lines = text.splitlines(keepends=True)
                changed = False
                for i, line in enumerate(lines):
                    original = line
                    for key in ordered_keys:
                        token = f"{{{{ {key} }}}}"
                        pattern = patterns[key]
                        if pattern.search(line):
                            line = pattern.sub(token, line)
                            write_log(f"{path}:{i+1} {mapping[key]} -> {token}", log_file, verbose)
                    if line != original:
                        lines[i] = line
                        changed = True
                if changed:
                    path.write_text("".join(lines), encoding="utf-8")


def revert_context(
    src: Path,
    dst: Path,
    profile: Path,
    *,
    log_file: Path = Path(os.devnull),
    verbose: bool = False,
) -> None:
    """Copy project and replace private values with tokens using profile."""
    copy_project(src, dst)
    mapping = load_profile(profile)
    replace_values_with_tokens(dst, mapping, log_file, verbose)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Revert template context")
    parser.add_argument("src", type=Path, help="Private project directory")
    parser.add_argument("dst", type=Path, help="Destination directory")
    parser.add_argument("profile", type=Path, help="YAML profile with values")
    parser.add_argument("--verbose", action="store_true", help="Print log to stdout")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_file = get_log_file("revert")
    revert_context(args.src, args.dst, args.profile, log_file=log_file, verbose=args.verbose)


if __name__ == "__main__":
    main()
