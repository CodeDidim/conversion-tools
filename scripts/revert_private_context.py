import argparse
import os
from pathlib import Path
from typing import Dict

from scripts.inject_private_context import load_profile, copy_project

TEXT_EXTENSIONS = {".py", ".robot", ".yaml", ".md"}


def replace_values_with_tokens(base_dir: Path, mapping: Dict[str, str]) -> None:
    """Replace private values with ``{{ KEY }}`` tokens in text files."""
    for root, _, files in os.walk(base_dir):
        for name in files:
            path = Path(root) / name
            if path.suffix in TEXT_EXTENSIONS:
                text = path.read_text(encoding="utf-8")
                new_text = text
                for key, value in mapping.items():
                    token = f"{{{{ {key} }}}}"
                    new_text = new_text.replace(value, token)
                if new_text != text:
                    path.write_text(new_text, encoding="utf-8")


def revert_context(src: Path, dst: Path, profile: Path) -> None:
    """Copy project and replace private values with tokens using profile."""
    copy_project(src, dst)
    mapping = load_profile(profile)
    replace_values_with_tokens(dst, mapping)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Revert private context")
    parser.add_argument("src", type=Path, help="Private project directory")
    parser.add_argument("dst", type=Path, help="Destination directory")
    parser.add_argument("profile", type=Path, help="YAML profile with values")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    revert_context(args.src, args.dst, args.profile)


if __name__ == "__main__":
    main()
