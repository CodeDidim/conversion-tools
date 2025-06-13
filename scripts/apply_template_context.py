import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

# Ensure this script works when executed directly from the ``scripts`` folder.
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.constants import TEXT_EXTENSIONS


LOG_DIR = Path("log")


def get_log_file(script_name: str) -> Path:
    """Return a log file path inside LOG_DIR with timestamp."""
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"{script_name}_{timestamp}.log"


def write_log(message: str, log_file: Path, verbose: bool) -> None:
    """Append a log message using UTF-8 encoding."""
    with log_file.open("a", encoding="utf-8") as f:
        f.write(message + "\n")
    if verbose:
        print(message)


def load_profile(path: Path) -> Dict[str, str]:
    """Load YAML profile using proper YAML parser."""
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")

    data = None
    if yaml is not None:
        try:
            data = yaml.safe_load(content) or {}
        except yaml.YAMLError:
            data = None

    if data is None:
        data = {}
        for lineno, line in enumerate(content.splitlines(), 1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if ":" not in line:
                raise ValueError(
                    f"❌ Invalid line {lineno!r} in profile {path}\n"
                    "Each line must be in 'KEY: value' format."
                )
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if not key:
                raise ValueError(
                    f"❌ Missing key on line {lineno} in profile {path}\n"
                    "Ensure lines use 'KEY: value' syntax."
                )
            data[key] = value
    else:
        if not isinstance(data, dict):
            raise ValueError(
                f"❌ Profile {path} must contain a mapping\n"
                "Verify the YAML structure or regenerate the profile from examples."
            )
        for key, value in list(data.items()):
            if not isinstance(key, str):
                raise ValueError(
                    f"❌ Profile key must be string, got {type(key)}\n"
                    "Check for missing quotes around keys."
                )
            if not isinstance(value, str):
                data[key] = str(value)

    return data


def copy_project(src: Path, dst: Path) -> None:
    """Copy ``src`` directory tree to ``dst``."""
    shutil.copytree(src, dst)


def overlay_files(
    overlay_dir: Path, target_dir: Path, log_file: Path, verbose: bool
) -> None:
    """Overlay files with symlink security checks."""
    for root, dirs, files in os.walk(overlay_dir):
        for name in files:
            src_path = Path(root) / name
            rel = src_path.relative_to(overlay_dir)
            dst_path = target_dir / rel

            if src_path.is_symlink():
                link_target = src_path.resolve()

                try:
                    link_target.relative_to(overlay_dir)
                except ValueError:
                    write_log(
                        f"⚠️  Skipping symlink {src_path} -> {link_target} (outside overlay)",
                        log_file,
                        verbose,
                    )
                    continue

                dst_path.parent.mkdir(parents=True, exist_ok=True)
                dst_path.symlink_to(os.readlink(src_path))
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)


def replace_tokens(base_dir: Path, mapping: Dict[str, str], log_file: Path, verbose: bool) -> None:
    """Replace ``{{ KEY }}`` tokens in text files under ``base_dir``."""
    patterns = {
        key: re.compile(r"\{\{\s*" + re.escape(key) + r"\s*\}\}")
        for key in mapping
    }
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
                        pattern = patterns[key]
                        if pattern.search(line):
                            line = pattern.sub(value, line)
                            write_log(
                                f"{path}:{i+1} {{{{ {key} }}}} -> {value}",
                                log_file,
                                verbose,
                            )
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
        overlay_files(overlay, dst, log_file, verbose)
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
