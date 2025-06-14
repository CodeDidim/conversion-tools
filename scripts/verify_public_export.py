import argparse
import os
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

if __package__ is None:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.constants import KEYWORDS
from core.utils import is_binary_file


Result = Tuple[bool, List[str], List[str]]  # ok, errors, warnings


def _clean_lines(lines: Iterable[str]) -> List[str]:
    cleaned = []
    for line in lines:
        lower = line.lower()
        if any(kw.lower() in lower for kw in KEYWORDS):
            continue
        cleaned.append(line)
    return cleaned


def _compare_files(template_file: Path, export_file: Path) -> Tuple[bool, Optional[str]]:
    """Compare two files. Return (match, reason).
    reason is 'cleaned' if export_file matches template_file with keyword lines removed.
    """
    if template_file.is_symlink() or export_file.is_symlink():
        return (os.readlink(template_file) == os.readlink(export_file), None)

    if is_binary_file(template_file):
        return (template_file.read_bytes() == export_file.read_bytes(), None)

    t_lines = template_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    e_lines = export_file.read_text(encoding="utf-8", errors="ignore").splitlines()

    if t_lines == e_lines:
        return (True, None)

    if _clean_lines(t_lines) == e_lines:
        return (False, "cleaned")

    return (False, "mismatch")


def verify_public_export(
    template_dir: Path, export_dir: Path, overlay_manifest: Optional[List[Path]] = None
) -> bool:
    """Verify that ``export_dir`` matches ``template_dir`` excluding overlay files."""
    overlay_set = {Path(p) for p in overlay_manifest or []}

    template_files = {
        p.relative_to(template_dir)
        for p in template_dir.rglob("*")
        if p.is_file() and p.relative_to(template_dir) not in overlay_set
    }
    export_files = {
        p.relative_to(export_dir)
        for p in export_dir.rglob("*")
        if p.is_file()
    }

    errors: List[str] = []
    warnings: List[str] = []

    missing = template_files - export_files
    for rel in sorted(missing):
        errors.append(f"Missing file: {rel}")

    unexpected = export_files - template_files
    for rel in sorted(unexpected):
        if rel in overlay_set:
            errors.append(f"{rel} found in export (overlay file)")
        else:
            errors.append(f"Unexpected file: {rel}")

    matched = template_files & export_files
    for rel in sorted(matched):
        t_file = template_dir / rel
        e_file = export_dir / rel
        same, reason = _compare_files(t_file, e_file)
        if not same:
            if reason == "cleaned":
                warnings.append(f"{rel} has cleaned lines")
            else:
                errors.append(f"{rel} content mismatch")

    for msg in errors:
        print(f"\u2717 Error: {msg}")
    for msg in warnings:
        print(f"\u26A0\ufe0f Warning: {msg}")

    if not errors:
        print(f"\u2713 Verified: {len(matched)} files match template")
    return not errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify public export matches template")
    parser.add_argument("template", type=Path)
    parser.add_argument("export", type=Path)
    parser.add_argument("--overlay-manifest", type=Path, help="Path to .overlay_manifest")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    overlay_files = None
    if args.overlay_manifest and args.overlay_manifest.exists():
        overlay_files = [Path(line.strip()) for line in args.overlay_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    ok = verify_public_export(args.template, args.export, overlay_files)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
