import argparse
import os
import shutil
from pathlib import Path
from typing import Dict, Optional

TEXT_EXTENSIONS = {".py", ".robot", ".yaml", ".md"}


def load_profile(path: Path) -> Dict[str, str]:
    """Load a very simple YAML file mapping keys to string values."""
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    with path.open("r") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("'\"")
    return data


def copy_project(src: Path, dst: Path) -> None:
    """Copy ``src`` directory tree to ``dst``."""
    shutil.copytree(src, dst)


def overlay_files(overlay_dir: Path, target_dir: Path) -> None:
    """Overlay files from ``overlay_dir`` onto ``target_dir``."""
    for root, dirs, files in os.walk(overlay_dir):
        for name in files:
            src_path = Path(root) / name
            rel = src_path.relative_to(overlay_dir)
            dst_path = target_dir / rel
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)


def replace_tokens(base_dir: Path, mapping: Dict[str, str]) -> None:
    """Replace ``{{ KEY }}`` tokens in text files under ``base_dir``."""
    for root, dirs, files in os.walk(base_dir):
        for name in files:
            path = Path(root) / name
            if path.suffix in TEXT_EXTENSIONS:
                text = path.read_text()
                new_text = text
                for key, value in mapping.items():
                    token = f"{{{{ {key} }}}}"
                    new_text = new_text.replace(token, value)
                if new_text != text:
                    path.write_text(new_text)


def inject_context(src: Path, dst: Path, profile: Path, overlay: Optional[Path] = None) -> None:
    """Copy project and replace tokens using profile, applying optional overlay."""
    copy_project(src, dst)
    if overlay:
        overlay_files(overlay, dst)
    mapping = load_profile(profile)
    replace_tokens(dst, mapping)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inject private context")
    parser.add_argument("src", type=Path, help="Generic project directory")
    parser.add_argument("dst", type=Path, help="Destination directory")
    parser.add_argument("profile", type=Path, help="YAML profile with values")
    parser.add_argument("--overlay", type=Path, default=None, help="Overlay directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inject_context(args.src, args.dst, args.profile, args.overlay)


if __name__ == "__main__":
    main()
