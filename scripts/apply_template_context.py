import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# File extensions and special file names treated as text for token replacement
TEXT_EXTENSIONS = {
    ".py",
    ".robot",
    ".yaml",
    ".md",
    ".txt",
    ".toml",
    ".sh",
    ".ps1",
    ".yml",
    ".gitignore",
    ".dockerignore",
    ".in",
    ".example",
    ".validate",
    ".excalidraw",
}

LOG_DIR = Path("log")


def get_log_file(script_name: str) -> Path:
    """Return a log file path inside LOG_DIR with timestamp."""
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"{script_name}_{timestamp}.log"


def write_log(message: str, log_file: Path, verbose: bool) -> None:
    with log_file.open("a") as f:
        f.write(message + "\n")
    if verbose:
        print(message)


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


def replace_tokens(base_dir: Path, mapping: Dict[str, str], log_file: Path, verbose: bool) -> None:
    """Replace ``{{ KEY }}`` tokens in text files under ``base_dir``."""
    for root, dirs, files in os.walk(base_dir):
        for name in files:
            path = Path(root) / name
            if path.suffix in TEXT_EXTENSIONS or path.name in TEXT_EXTENSIONS:
                text = path.read_text(encoding="utf-8")
                lines = text.splitlines(keepends=True)
                changed = False
                for i, line in enumerate(lines):
                    original = line
                    for key, value in mapping.items():
                        token = f"{{{{ {key} }}}}"
                        if token in line:
                            line = line.replace(token, value)
                            write_log(f"{path}:{i+1} {token} -> {value}", log_file, verbose)
                    if line != original:
                        lines[i] = line
                        changed = True
                if changed:
                    path.write_text("".join(lines), encoding="utf-8")


def inject_context(
    src: Path,
    dst: Path,
    profile: Path,
    overlay: Optional[Path] = None,
    *,
    log_file: Path = Path(os.devnull),
    verbose: bool = False,
) -> None:
    """Copy project and replace tokens using profile, applying optional overlay."""
    copy_project(src, dst)
    if overlay:
        overlay_files(overlay, dst)
    mapping = load_profile(profile)
    replace_tokens(dst, mapping, log_file, verbose)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply template context")
    parser.add_argument("src", type=Path, help="Generic project directory")
    parser.add_argument("dst", type=Path, help="Destination directory")
    parser.add_argument("profile", type=Path, help="YAML profile with values")
    parser.add_argument("--overlay", type=Path, default=None, help="Overlay directory")
    parser.add_argument("--verbose", action="store_true", help="Print log to stdout")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_file = get_log_file("apply")
    inject_context(args.src, args.dst, args.profile, args.overlay, log_file=log_file, verbose=args.verbose)


if __name__ == "__main__":
    main()
