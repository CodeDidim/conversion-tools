from pathlib import Path
import argparse
import sys
import subprocess
import json
import os
import shutil
from urllib import request
from typing import Optional, Tuple, Set, Iterable, List, Dict
import re

from core.rollback import RollbackManager
from scripts.apply_template_context import inject_context, load_profile
from scripts.export_to_public import export_directory
from scripts.validate_public_repo import validate_directory
from core.constants import TEXT_EXTENSIONS, KEYWORDS
from core.utils import is_binary_file
from scripts.manage_logs import cleanup_logs
from scripts.verify_public_export import verify_public_export

DEFAULT_CONFIG = Path('.workflow-config.yaml')

rollback_manager = RollbackManager(Path('.'))


class WorkflowManager:
    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize paths so the workflow works from any directory."""
        # Directory where workflow.py lives
        self.workflow_dir = Path(__file__).resolve().parent

        # Project directory (where we're applying templates)
        self.root_dir = project_dir or Path.cwd()

        # Config in project directory
        self.config_file = self.root_dir / ".workflow-config.yaml"

        # Scripts are relative to workflow.py
        self.conversion_tools_dir = self.workflow_dir
        self.scripts_dir = self.workflow_dir / "scripts"

        # Ensure scripts directory exists
        if not self.scripts_dir.exists():
            print(f"❌ Scripts directory not found: {self.scripts_dir}")
            print(f"   Expected to find it relative to {self.workflow_dir}")
            sys.exit(1)

        self.load_config()
        self.setup_github_manager()

    def load_config(self) -> None:
        """Load configuration from the project directory."""
        if self.config_file.exists():
            self.config = load_profile(self.config_file)
        else:
            self.config = {}

    def setup_github_manager(self) -> None:  # pragma: no cover - simple stub
        """Placeholder for GitHub-related setup."""
        self.github_manager = None

    def to_private(self) -> None:  # pragma: no cover - CLI helper
        """Convert public code to private."""
        print("\n🔄 Converting to PRIVATE mode...")

        temp_dir = self.root_dir / ".workflow-temp"

        # Apply private template
        print("→ Applying private templates...")
        apply_script = self.scripts_dir / "apply_template_context.py"

        # Make sure the script exists
        if not apply_script.exists():
            print(f"❌ Script not found: {apply_script}")
            sys.exit(1)

        cmd = [
            sys.executable,
            str(apply_script),
            str(self.root_dir),
            str(temp_dir),
            str(self.conversion_tools_dir / self.config.get("profile", "")),
            "--verbose",
        ]
        subprocess.run(cmd, check=True)

def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    return load_profile(path)


def repo_is_public(owner: str, repo: str) -> bool:
    """Return True if the GitHub repo is public."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = request.Request(url, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    with request.urlopen(req) as resp:
        data = json.load(resp)
    return not data.get("private", True)


def get_repo_fields(cfg: dict) -> Tuple[Optional[str], Optional[str]]:
    """Extract GitHub ``owner`` and ``repo`` from configuration."""

    owner = cfg.get("github.owner")
    repo = cfg.get("github.repo")
    github = cfg.get("github")
    if isinstance(github, dict):
        owner = owner or github.get("owner")
        repo = repo or github.get("repo")
    owner = owner or cfg.get("owner")
    repo = repo or cfg.get("repo")
    return owner, repo


def repo_status(cfg: dict) -> str:
    """Return 'public' or 'private' based on GitHub visibility."""

    owner, repo = get_repo_fields(cfg)


    if not owner or not repo:
        raise SystemExit(
            "❌ github.owner and github.repo must be set in config\n"
            "\n"
            "Copy examples/.workflow-config.yaml.example, update owner/repo, and\n"
            "place it as .workflow-config.yaml in your project."
        )
    return "public" if repo_is_public(owner, repo) else "private"


COMMON_WORDS = {"and", "the", "for", "or"}
TEST_PATTERNS = ["TEST", "EMPTY", "DUMMY", "EXAMPLE", "TODO"]
GENERIC_NAMES = {"TOKEN", "KEY", "VALUE", "SECRET"}


def is_valid_placeholder(key: str) -> bool:
    """Return True if ``key`` looks like a real placeholder."""
    if len(key) < 3:
        return False
    if key.lower() in COMMON_WORDS:
        return False
    if any(p in key.upper() for p in TEST_PATTERNS):
        return False
    if key.upper() in GENERIC_NAMES:
        return False
    if key.islower():
        return False
    if re.search(r"[^A-Za-z0-9_]", key):
        return False
    return True


def _load_placeholder_ignore(template_dir: Path) -> Set[str]:
    """Return a set of placeholders listed in ``.placeholderignore``."""
    ignore: Set[str] = set()
    ignore_file = template_dir / ".placeholderignore"
    if ignore_file.exists():
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                ignore.add(line)
    return ignore


def find_all_placeholders(template_dir: Path, ignore: Iterable[str] = ()) -> Set[str]:
    """Return all unique valid ``{{ KEY }}`` placeholders found under ``template_dir``."""
    placeholders: Set[str] = set()
    ignore_set = set(ignore)
    pattern = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
    for root, _, files in os.walk(template_dir):
        for name in files:
            path = Path(root) / name
            if path.is_symlink():
                try:
                    path = path.resolve(strict=True)
                except FileNotFoundError:
                    continue
            if is_binary_file(path):
                continue
            if path.suffix in TEXT_EXTENSIONS or path.name in TEXT_EXTENSIONS:
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                for match in pattern.finditer(text):
                    key = match.group(1)
                    if key in ignore_set:
                        continue
                    if is_valid_placeholder(key):
                        placeholders.add(key)
    return placeholders


def _append_missing_keys(profile_path: Path, keys: Iterable[str]) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    content = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
    newline = "" if not content or content.endswith("\n") else "\n"
    with profile_path.open("a", encoding="utf-8") as f:
        f.write(newline)
        for key in sorted(keys):
            f.write(f"{key}: TODO\n")


def validate_profile(template_dir: Path, profile_path: Path) -> bool:
    """Validate that profile contains keys for all placeholders.

    Missing keys are reported and optionally appended to the profile when running
    in an interactive session or when ``CONVERSION_AUTO_APPEND`` environment
    variable is set to ``1``/``true``.
    """

    profile_data = load_profile(profile_path)
    ignore = _load_placeholder_ignore(template_dir)
    extra = profile_data.get("ignore_placeholders")
    if isinstance(extra, list):
        ignore.update(str(x) for x in extra if isinstance(x, str))
    elif isinstance(extra, str):
        for item in extra.split(','):
            item = item.strip()
            if item:
                ignore.add(item)
    required = find_all_placeholders(template_dir, ignore)
    existing = set(k for k in profile_data.keys() if k != "ignore_placeholders")
    missing = required - existing

    if not missing:
        return True

    print("\u26A0\uFE0F  Missing placeholders in profile:")
    for key in sorted(missing):
        print(f"  - {key}")

    auto_env = os.getenv("CONVERSION_AUTO_APPEND", "").lower() in {"1", "true", "yes"}
    if auto_env or sys.stdin.isatty():
        if not auto_env:
            ans = input(f"\nAppend to {profile_path.name}? [Y/n]: ").strip().lower()
            if ans not in {"", "y", "yes"}:
                return False
        _append_missing_keys(profile_path, missing)
        full_path = profile_path.resolve()
        plural = "s" if len(missing) != 1 else ""
        print(
            f"\u2713 Updated profile file: {full_path} - added {len(missing)} missing key{plural} (marked as TODO)"
        )
        return True

    print("Run interactively or set CONVERSION_AUTO_APPEND=1 to update the profile automatically.")
    return False


def validate_workflow_setup(config_path: Path = DEFAULT_CONFIG) -> bool:
    """Validate configuration, template, profile and safety checks."""
    print("\n🔍 Validating workflow setup...\n")

    errors: List[str] = []
    warnings: List[str] = []
    auto_fix = os.getenv("CONVERSION_AUTO_FIX", "").lower() in {"1", "true", "yes"}

    cfg: dict = {}
    if not config_path.exists():
        errors.append(f"Config file '{config_path}' not found")
    else:
        try:
            cfg = load_profile(config_path)
        except Exception as exc:
            errors.append(str(exc))

    required = ["template", "profile"]
    for key in required:
        if key not in cfg:
            errors.append(f"Missing required config field: {key}")

    template = Path(cfg.get("template", "template"))
    profile_path = Path(cfg.get("profile", "profile.yaml"))
    overlay = Path(cfg.get("overlay_dir", "private-overlay"))

    if "template" in cfg and not template.exists():
        errors.append(f"Template directory '{template}' not found (did you mean 'template'?)")
    if "profile" in cfg and not profile_path.exists():
        errors.append(f"Profile file '{profile_path}' not found")
    if cfg.get("overlay_dir") and not overlay.exists():
        warnings.append(f"Overlay directory '{overlay}' not found")

    try:
        t_res = template.resolve()
        p_res = profile_path.resolve()
        o_res = overlay.resolve()
        if t_res in p_res.parents or p_res in t_res.parents:
            errors.append("Circular reference between template and profile")
        if o_res in t_res.parents or t_res in o_res.parents:
            errors.append("Circular reference between template and overlay_dir")
    except Exception:
        pass

    if profile_path.exists():
        try:
            pdata = load_profile(profile_path)
        except Exception as exc:  # pragma: no cover - error message tested via return value
            errors.append(str(exc))
        else:
            for key, val in pdata.items():
                if isinstance(val, str) and re.search(r"\{\{.*\}\}", val):
                    errors.append(f"Profile contains invalid placeholder syntax for {key}")
                if not isinstance(val, str):
                    warnings.append(f"Value for {key} converted to string")
                trimmed = str(val).strip()
                if trimmed.upper() in {"", "TODO", "FIXME"}:
                    warnings.append(f"Profile missing value for: {key}")
                if " " in key or "-" in key:
                    warnings.append(f"Possible typo in key name: {key}")

    if template.exists():
        for f in template.rglob("*"):
            if f.is_file():
                if is_binary_file(f):
                    try:
                        text = f.read_text(encoding="utf-8")
                    except Exception:
                        text = ""
                    if "{{" in text and "}}" in text:
                        warnings.append(f"Placeholder in non-text file: {f}")
                else:
                    try:
                        text = f.read_text(encoding="utf-8")
                    except Exception:
                        continue
                    if "{{ {{" in text:
                        errors.append(f"Nested placeholder found in {f}")
                    for m in re.finditer(r"\{\{\s*([^\s{}]+)\s*\}\}", text):
                        key = m.group(1)
                        if not re.fullmatch(r"[A-Z0-9_]+", key):
                            warnings.append(f"Inconsistent placeholder '{key}' in {f}")

    gitignore = Path(".gitignore")
    gitignore_lines: List[str] = []
    if not gitignore.exists():
        warnings.append(".gitignore not found")
    else:
        gitignore_lines = gitignore.read_text(encoding="utf-8").splitlines()

    def ensure_ignored(entry: str) -> bool:
        if entry not in gitignore_lines:
            warnings.append(f"{entry} is not in .gitignore")
            if auto_fix:
                gitignore_lines.append(entry)
                return True
        return False

    changed = False
    changed |= ensure_ignored(".workflow-config.yaml")
    changed |= ensure_ignored(str(overlay))

    if changed and gitignore.exists():
        gitignore.write_text("\n".join(gitignore_lines) + "\n", encoding="utf-8")

    if overlay.exists() and Path(".git").exists():
        res = subprocess.run(["git", "ls-files", str(overlay)], capture_output=True, text=True)
        if res.stdout.strip():
            errors.append("Private overlay files appear tracked by git")
    if profile_path.exists() and Path(".git").exists():
        res = subprocess.run(["git", "ls-files", str(profile_path)], capture_output=True, text=True)
        if res.stdout.strip():
            errors.append("Profile file appears tracked by git")

    if errors:
        print("❌ ERRORS (must fix):")
        for e in errors:
            print(f"- {e}")
    if warnings:
        print("⚠️  WARNINGS (recommended fixes):")
        for w in warnings:
            print(f"- {w}")
    if auto_fix and changed:
        print("✓ Auto-fixed .gitignore entries")

    return not errors


def validate_before_workflow(config_path: Path, operation: str) -> Tuple[bool, List[str], List[str]]:
    """Validate before running workflow.

    Returns: (is_valid, errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    cfg: dict = {}
    if not config_path.exists():
        errors.append(f"Config file not found: {config_path}")
        return False, errors, warnings

    try:
        cfg = load_profile(config_path)
    except Exception as exc:
        errors.append(str(exc))
        return False, errors, warnings

    template = Path(cfg.get("template", "template"))
    profile_path = Path(cfg.get("profile", "profile.yaml"))
    overlay = Path(cfg.get("overlay_dir", "private-overlay"))
    temp_dir = Path(cfg.get("temp_dir", ".workflow-temp"))

    if not template.exists():
        errors.append(f"Template directory missing: {template}")
    if not profile_path.exists():
        errors.append(f"Profile file missing: {profile_path}")
    if cfg.get("overlay_dir") and not overlay.exists():
        warnings.append(f"Overlay directory missing: {overlay}")

    try:
        t = template.resolve()
        o = overlay.resolve()
        tmp = temp_dir.resolve()
        if t == o or t == tmp or o == tmp:
            errors.append("template, overlay_dir and temp_dir must be distinct paths")
    except Exception:
        pass

    placeholder_styles: Set[str] = set()
    placeholders: Set[str] = set()
    placeholder_map: Dict[str, List[Tuple[str, int]]] = {}
    if template.exists():
        for root, _, files in os.walk(template):
            for name in files:
                path = Path(root) / name
                if path.is_symlink():
                    try:
                        path = path.resolve(strict=True)
                    except FileNotFoundError:
                        continue
                if is_binary_file(path):
                    try:
                        data = path.read_bytes()
                    except Exception:
                        data = b""
                    if b"{{" in data and b"}}" in data:
                        errors.append(f"Placeholder found in binary file: {path}")
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if "{{ {{" in text:
                    errors.append(f"Nested placeholder found in {path}")
                for lineno, line in enumerate(text.splitlines(), 1):
                    for m in re.finditer(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", line):
                        key = m.group(1)
                        placeholders.add(key)
                        placeholder_styles.add(m.group(0).replace(key, "KEY"))
                        placeholder_map.setdefault(key, []).append((str(path), lineno))
                        if not re.fullmatch(r"[A-Z0-9_]+", key):
                            warnings.append(
                                f"Inconsistent placeholder '{key}' in {path}"
                            )
        if len(placeholder_styles) > 1:
            warnings.append("Inconsistent placeholder style used in template")

    profile_data: Dict[str, str] = {}
    if profile_path.exists():
        try:
            profile_data = load_profile(profile_path)
        except Exception as exc:
            errors.append(str(exc))
        else:
            for key, val in profile_data.items():
                if isinstance(val, str) and re.search(r"\{\{.*\}\}", val):
                    errors.append(f"Profile value for {key} contains placeholder syntax")
                if not isinstance(val, str):
                    warnings.append(f"Value for {key} converted to string")

    if placeholders:
        missing = placeholders - set(profile_data.keys())
        if missing:
            details = []
            for key in sorted(missing):
                locs = placeholder_map.get(key, [])
                loc_str = "; ".join(f"{p}:{ln}" for p, ln in locs)
                if loc_str:
                    details.append(f"{key} ({loc_str})")
                else:
                    details.append(key)
            errors.append("Profile missing keys: " + ", ".join(details))

    gitignore = Path(".gitignore")
    if gitignore.exists():
        lines = gitignore.read_text(encoding="utf-8").splitlines()
        for entry in [".workflow-config.yaml", str(overlay)]:
            if entry not in lines:
                warnings.append(f"{entry} missing from .gitignore")
    else:
        warnings.append(".gitignore not found")

    if template.exists():
        for f in template.rglob("*"):
            if f.is_file() and not is_binary_file(f):
                txt = f.read_text(encoding="utf-8", errors="ignore")
                if any(kw.lower() in txt.lower() for kw in KEYWORDS):
                    errors.append(f"Private reference found in template: {f}")
                    break

    if overlay.exists() and Path(".git").exists():
        res = subprocess.run(["git", "ls-files", str(overlay)], capture_output=True, text=True)
        if res.stdout.strip():
            errors.append("Overlay directory appears tracked by git")

    if Path(".git").exists():
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if res.stdout.strip():
            warnings.append("Git repository has uncommitted changes")

    return not errors, errors, warnings


def private_workflow(
    config_path: Path = DEFAULT_CONFIG,
    *,
    dry_run: bool = False,
) -> Path:
    valid, errors, warnings = validate_before_workflow(config_path, "private")
    if not valid:
        for e in errors:
            print(f"❌ {e}")
        for w in warnings:
            print(f"⚠️  {w}")
        raise SystemExit("❌ Workflow validation failed")

    cfg = load_config(config_path)
    temp_dir = Path(cfg.get('temp_dir', '.workflow-temp'))
    template = Path(cfg.get('template', 'template'))
    profile = Path(cfg.get('profile', 'scripts/config_profiles/company_profile.yaml'))
    overlay = Path(cfg.get('overlay_dir', 'private-overlay'))
    dst = temp_dir / 'private'
    if not validate_profile(template, profile):
        raise SystemExit('❌ Profile validation failed')
    rollback_id = None
    if not dry_run:
        rollback_id = rollback_manager.create_snapshot('to_private', cfg)
        try:
            inject_context(template, dst, profile, overlay)
            if overlay.exists():
                _write_overlay_manifest(overlay, dst)
        except Exception:
            rollback_manager.rollback_to(rollback_id)
            raise
    return dst


def _write_overlay_manifest(overlay_dir: Path, target_dir: Path) -> None:
    """Write list of overlay files relative to ``target_dir``."""
    manifest = target_dir / ".overlay_manifest"
    lines = []
    for root, _, files in os.walk(overlay_dir):
        for name in files:
            rel = Path(root) / name
            rel = rel.relative_to(overlay_dir)
            lines.append(str(rel))
    manifest.write_text("\n".join(lines), encoding="utf-8")


def _read_overlay_manifest(private_dir: Path) -> Optional[List[Path]]:
    manifest = private_dir / ".overlay_manifest"
    if not manifest.exists():
        return None
    lines = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [Path(line) for line in lines]


def _remove_overlay(
    public_dir: Path, template: Path, overlay: Path, overlay_files: Optional[Iterable[Path]] = None
) -> None:
    """Remove files introduced by the overlay from ``public_dir``."""
    if overlay_files is None:
        if not overlay.exists():
            return
        overlay_files = []
        for root, _, files in os.walk(overlay):
            for name in files:
                rel = Path(root) / name
                rel = rel.relative_to(overlay)
                overlay_files.append(rel)

    for rel in overlay_files:
        target = public_dir / rel
        template_file = template / rel
        if template_file.exists():
            if target.exists() or target.is_symlink():
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            if template_file.is_symlink():
                target.symlink_to(os.readlink(template_file))
            else:
                shutil.copy2(template_file, target)
        else:
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            elif target.exists() or target.is_symlink():
                target.unlink()

    # Clean up empty directories that came from the overlay
    for root, dirs, files in os.walk(public_dir, topdown=False):
        path = Path(root)
        try:
            next(path.iterdir())
        except StopIteration:
            path.rmdir()


def public_workflow(
    config_path: Path = DEFAULT_CONFIG,
    *,
    dry_run: bool = False,
) -> Path:
    valid, errors, warnings = validate_before_workflow(config_path, "public")
    if not valid:
        for e in errors:
            print(f"❌ {e}")
        for w in warnings:
            print(f"⚠️  {w}")
        raise SystemExit("❌ Workflow validation failed")

    cfg = load_config(config_path)
    temp_dir = Path(cfg.get('temp_dir', '.workflow-temp'))
    template = Path(cfg.get('template', 'template'))
    overlay = Path(cfg.get('overlay_dir', 'private-overlay'))
    public_dir = temp_dir / 'public'
    export_dir = temp_dir / 'export'
    private_dir = temp_dir / 'private'

    rollback_id = None
    if not dry_run:
        rollback_id = rollback_manager.create_snapshot('to_public', cfg)
        try:
            if public_dir.exists():
                shutil.rmtree(public_dir)
            shutil.copytree(template, public_dir, symlinks=True)
            overlay_files = _read_overlay_manifest(private_dir)
            _remove_overlay(public_dir, template, overlay, overlay_files)
            export_directory(public_dir, export_dir)
            validate_directory(export_dir)
            verify_files = (
                [p for p in overlay_files if not (template / p).exists()]
                if overlay_files
                else None
            )
            if not verify_public_export(template, export_dir, verify_files):
                raise SystemExit('❌ Public export verification failed')
        except Exception:
            rollback_manager.rollback_to(rollback_id)
            raise
    return export_dir


def _rollback_cli(args: argparse.Namespace) -> None:
    if args.list:
        for snap in rollback_manager.list_snapshots():
            print(f"{snap['timestamp']} - {snap.get('operation', '')}")
        return

    snapshot_id = None
    if args.to:
        snapshot_id = args.to
    elif args.steps is not None:
        snaps = rollback_manager.list_snapshots()
        if len(snaps) > args.steps:
            snapshot_id = snaps[args.steps].get("timestamp")
    else:
        snaps = rollback_manager.list_snapshots()
        if snaps:
            snapshot_id = snaps[0]["timestamp"]

    if not snapshot_id:
        print("No snapshot found")
        return
    if rollback_manager.rollback_to(snapshot_id, dry_run=args.dry_run):
        print(f"Rolled back to {snapshot_id}")
    else:
        print("Rollback failed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Workflow helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("private")
    sub.add_parser("public")
    roll = sub.add_parser("rollback")
    roll.add_argument("--list", action="store_true")
    roll.add_argument("--to", type=str)
    roll.add_argument("--steps", type=int)
    roll.add_argument("--dry-run", action="store_true")
    sub.add_parser("clean-logs", help="Clean up old log files")
    sub.add_parser("status", help="Show repository visibility")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    def ensure_config(path: Path) -> None:
        if not path.exists():
            raise SystemExit(f"\u274c Config file not found: {path}")

    if args.command == "private":
        ensure_config(args.config)
        private_workflow(args.config, dry_run=args.dry_run)
    elif args.command == "public":
        ensure_config(args.config)
        public_workflow(args.config, dry_run=args.dry_run)
    elif args.command == "rollback":
        _rollback_cli(args)
    elif args.command == "clean-logs":
        cleanup_logs(Path("log"), 30)
    elif args.command == "status":
        config_path = Path(args.config)
        print(f"Using config file: {config_path.resolve()}")
        ensure_config(config_path)
        cfg = load_config(config_path)
        vis = repo_status(cfg)
        print(f"Repository is {vis}")


if __name__ == "__main__":
    main()



