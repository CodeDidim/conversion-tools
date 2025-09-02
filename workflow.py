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
from scripts.validate_public_repo import validate_directory
from core.constants import TEXT_EXTENSIONS, KEYWORDS
from core.utils import is_binary_file
from scripts.manage_logs import cleanup_logs
from scripts.verify_public_export import verify_public_export
import yaml

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
            self.config = load_config(self.config_file)
        else:
            self.config = {}

    def setup_github_manager(self) -> None:  # pragma: no cover - simple stub
        """Placeholder for GitHub-related setup."""
        self.github_manager = None

    def to_private(self) -> None:  # pragma: no cover - CLI helper
        """Convert public code to private."""
        print("\n🔄 Converting to PRIVATE mode...")

        working_directory = self.root_dir / ".workflow-temp"

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
            str(working_directory),
            str(self.conversion_tools_dir / self.config.get("placeholder_values", "")),
            "--verbose",
        ]
        subprocess.run(cmd, check=True)

def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    config = yaml.safe_load(open(path))

    if "profile" in config and "placeholder_values" not in config:
        config["placeholder_values"] = config["profile"]
        print("Warning: 'profile' is deprecated, use 'placeholder_values' instead")

    if "template" in config and "template_source_dir" not in config:
        config["template_source_dir"] = config["template"]
        print("Warning: 'template' is deprecated, use 'template_source_dir' instead")

    if "temp_dir" in config and "working_directory" not in config:
        config["working_directory"] = config["temp_dir"]
        print("Warning: 'temp_dir' is deprecated, use 'working_directory' instead")

    if "overlay_dir" in config and "company_only_files" not in config:
        config["company_only_files"] = config["overlay_dir"]
        print("Warning: 'overlay_dir' is deprecated, use 'company_only_files' instead")

    return config


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
    """Validate configuration, template, placeholder values and safety checks."""
    print("\n🔍 Validating workflow setup...\n")

    errors: List[str] = []
    warnings: List[str] = []
    auto_fix = os.getenv("CONVERSION_AUTO_FIX", "").lower() in {"1", "true", "yes"}

    cfg: dict = {}
    if not config_path.exists():
        errors.append(f"Config file '{config_path}' not found")
    else:
        try:
            cfg = load_config(config_path)
        except Exception as exc:
            errors.append(str(exc))

    required = ["template_source_dir", "placeholder_values"]
    for key in required:
        if key not in cfg:
            errors.append(f"Missing required config field: {key}")

    template = Path(cfg.get("template_source_dir", "template"))
    placeholder_values_path = Path(cfg.get("placeholder_values", "profile.yaml"))
    company_only_files = Path(cfg.get("company_only_files", "private-overlay"))

    if "template_source_dir" in cfg and not template.exists():
        errors.append(
            f"Template directory '{template}' not found (did you mean 'template_source_dir'?)"
        )
    if "placeholder_values" in cfg and not placeholder_values_path.exists():
        errors.append(f"Placeholder values file '{placeholder_values_path}' not found")
    if cfg.get("company_only_files") and not company_only_files.exists():
        warnings.append(f"Company-only files directory '{company_only_files}' not found")

    try:
        t_res = template.resolve()
        p_res = placeholder_values_path.resolve()
        o_res = company_only_files.resolve()
        if t_res in p_res.parents or p_res in t_res.parents:
            errors.append("Circular reference between template_source_dir and placeholder_values")
        if o_res in t_res.parents or t_res in o_res.parents:
            errors.append("Circular reference between template_source_dir and company_only_files")
    except Exception:
        pass

    if placeholder_values_path.exists():
        try:
            pdata = load_profile(placeholder_values_path)
        except Exception as exc:  # pragma: no cover - error message tested via return value
            errors.append(str(exc))
        else:
            for key, val in pdata.items():
                if isinstance(val, str) and re.search(r"\{\{.*\}\}", val):
                    errors.append(
                        f"Placeholder values file contains invalid placeholder syntax for {key}"
                    )
                if not isinstance(val, str):
                    warnings.append(f"Value for {key} converted to string")
                trimmed = str(val).strip()
                if trimmed.upper() in {"", "TODO", "FIXME"}:
                    warnings.append(f"Placeholder values missing value for: {key}")
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
    changed |= ensure_ignored(str(company_only_files))

    if changed and gitignore.exists():
        gitignore.write_text("\n".join(gitignore_lines) + "\n", encoding="utf-8")

    if company_only_files.exists() and Path(".git").exists():
        res = subprocess.run(
            ["git", "ls-files", str(company_only_files)], capture_output=True, text=True
        )
        if res.stdout.strip():
            errors.append("Company-only files directory appears tracked by git")
    if placeholder_values_path.exists() and Path(".git").exists():
        res = subprocess.run(
            ["git", "ls-files", str(placeholder_values_path)], capture_output=True, text=True
        )
        if res.stdout.strip():
            errors.append("Placeholder values file appears tracked by git")

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
        cfg = load_config(config_path)
    except Exception as exc:
        errors.append(str(exc))
        return False, errors, warnings

    template = Path(cfg.get("template_source_dir", "template"))
    placeholder_values_path = Path(cfg.get("placeholder_values", "profile.yaml"))
    company_only_files = Path(cfg.get("company_only_files", "private-overlay"))
    working_directory = Path(cfg.get("working_directory", ".workflow-temp"))

    if not template.exists():
        errors.append(f"Template directory missing: {template}")
    if not placeholder_values_path.exists():
        errors.append(f"Placeholder values file missing: {placeholder_values_path}")
    if cfg.get("company_only_files") and not company_only_files.exists():
        warnings.append(f"Company-only files directory missing: {company_only_files}")

    try:
        t = template.resolve()
        o = company_only_files.resolve()
        tmp = working_directory.resolve()
        if t == o or t == tmp or o == tmp:
            errors.append(
                "template_source_dir, company_only_files and working_directory must be distinct paths"
            )
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
    if placeholder_values_path.exists():
        try:
            profile_data = load_profile(placeholder_values_path)
        except Exception as exc:
            errors.append(str(exc))
        else:
            for key, val in profile_data.items():
                if isinstance(val, str) and re.search(r"\{\{.*\}\}", val):
                    errors.append(f"Placeholder values for {key} contains placeholder syntax")
                if not isinstance(val, str):
                    warnings.append(f"Value for {key} converted to string")

    # Add validation for placeholders in identifiers
    identifier_errors = []
    if template.exists() and placeholder_values_path.exists():
        class_def = re.compile(r'^\s*class\s+([^(:]+)', re.MULTILINE)
        func_def = re.compile(r'^\s*(?:async\s+)?def\s+([^(:]+)', re.MULTILINE)
        placeholder_pat = re.compile(r'\{\{\s*([A-Za-z0-9_]+)\s*\}\}')

        for root, _, files in os.walk(template):
            for name in files:
                path = Path(root) / name
                if path.suffix in {'.py', '.pyx', '.pyi'}:  # Python files
                    try:
                        text = path.read_text(encoding="utf-8")
                    except Exception:
                        continue

                    # Check class definitions
                    for m in class_def.finditer(text):
                        ident = m.group(1)
                        for ph in placeholder_pat.finditer(ident):
                            key = ph.group(1)
                            if key not in profile_data:
                                continue
                            value = str(profile_data[key])
                            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value.replace(' ', '')):
                                identifier_errors.append(
                                    f"{path}: Placeholder '{key}' in class name contains invalid identifier value: '{value}'"
                                )
                            elif ' ' in value:
                                warnings.append(
                                    f"{path}: Placeholder '{key}' in class name contains spaces: '{value}' - consider using a separate identifier key"
                                )

                    # Check function definitions
                    for m in func_def.finditer(text):
                        ident = m.group(1)
                        for ph in placeholder_pat.finditer(ident):
                            key = ph.group(1)
                            if key not in profile_data:
                                continue
                            value = str(profile_data[key])
                            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value.replace(' ', '')):
                                identifier_errors.append(
                                    f"{path}: Placeholder '{key}' in def name contains invalid identifier value: '{value}'"
                                )
                            elif ' ' in value:
                                warnings.append(
                                    f"{path}: Placeholder '{key}' in def name contains spaces: '{value}' - consider using a separate identifier key"
                                )

    errors.extend(identifier_errors)

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
        for entry in [".workflow-config.yaml", str(company_only_files)]:
            if entry not in lines:
                warnings.append(f"{entry} missing from .gitignore")
    else:
        warnings.append(".gitignore not found")

    if template.exists():
        private_msg = _find_private_references(template)
        if private_msg:
            errors.append(private_msg)

    if company_only_files.exists() and Path(".git").exists():
        res = subprocess.run(
            ["git", "ls-files", str(company_only_files)], capture_output=True, text=True
        )
        if res.stdout.strip():
            errors.append("Company-only files directory appears tracked by git")

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
    working_directory = Path(cfg.get('working_directory', '.workflow-temp'))
    template_source_dir = Path(cfg.get('template_source_dir', 'template'))
    placeholder_values = Path(
        cfg.get('placeholder_values', 'scripts/config_profiles/company_profile.yaml')
    )
    company_only_files = Path(cfg.get('company_only_files', 'private-overlay'))
    dst = working_directory / 'private'
    if not validate_profile(template_source_dir, placeholder_values):
        raise SystemExit('❌ Profile validation failed')
    rollback_id = None
    if not dry_run:
        rollback_id = rollback_manager.create_snapshot('to_private', cfg)
        try:
            inject_context(template_source_dir, dst, placeholder_values, company_only_files)
            if company_only_files.exists():
                _write_overlay_manifest(company_only_files, dst)
        except Exception:
            rollback_manager.rollback_to(rollback_id)
            raise
    return dst


def _write_overlay_manifest(company_only_files_dir: Path, target_dir: Path) -> None:
    """Write list of company-only files relative to ``target_dir``."""
    manifest = target_dir / ".overlay_manifest"
    lines = []
    for root, _, files in os.walk(company_only_files_dir):
        for name in files:
            rel = Path(root) / name
            rel = rel.relative_to(company_only_files_dir)
            lines.append(str(rel))
    manifest.write_text("\n".join(lines), encoding="utf-8")


def _read_overlay_manifest(private_dir: Path) -> Optional[List[Path]]:
    manifest = private_dir / ".overlay_manifest"
    if not manifest.exists():
        return None
    lines = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [Path(line) for line in lines]


def _remove_overlay(
    public_dir: Path,
    template: Path,
    company_only_files: Path,
    overlay_files: Optional[Iterable[Path]] = None,
) -> None:
    """Remove files introduced by the company-only overlay from ``public_dir``."""
    if overlay_files is None:
        if not company_only_files.exists():
            return
        overlay_files = []
        for root, _, files in os.walk(company_only_files):
            for name in files:
                rel = Path(root) / name
                rel = rel.relative_to(company_only_files)
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


def _find_private_references(template_dir: Path) -> Optional[str]:
    """Return formatted error message if private keywords are found."""

    hits: Dict[str, List[Tuple[int, str, str]]] = {}
    for f in template_dir.rglob("*"):
        if not f.is_file() or is_binary_file(f):
            continue
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, 1):
            for kw in KEYWORDS:
                if kw.lower() in line.lower():
                    info = hits.setdefault(str(f), [])
                    if len(info) < 3:
                        info.append((idx, line, kw))
                    break

    if not hits:
        return None

    details: List[str] = ["Private references found in template files:"]
    total = 0
    for path, items in hits.items():
        total += len(items)
        for idx, line, kw in items:
            text = line.strip()
            if len(text) > 80:
                text = text[:77] + "..."
            details.append(f"  {path}:{idx}: {text}")
            details.append(f"    → Found keyword: \"{kw}\"")
            details.append("    → Fix: Replace with {{ PLACEHOLDER }} placeholder")
        details.append("")
    summary = f"Found {total} private reference{'s' if total != 1 else ''} across {len(hits)} file{'s' if len(hits) != 1 else ''}"
    details.append(summary)
    details.append("Run `python workflow.py validate` to check exports.")
    details.append("See docs/DEVELOPMENT.md for template best practices.")
    return "\n".join(details).rstrip()


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
    working_directory = Path(cfg.get('working_directory', '.workflow-temp'))
    template_source_dir = Path(cfg.get('template_source_dir', 'template'))
    company_only_files = Path(cfg.get('company_only_files', 'private-overlay'))
    public_dir = working_directory / 'public'
    private_dir = working_directory / 'private'

    rollback_id = None
    if not dry_run:
        rollback_id = rollback_manager.create_snapshot('to_public', cfg)
        try:
            if public_dir.exists():
                shutil.rmtree(public_dir)
            shutil.copytree(template_source_dir, public_dir, symlinks=True)
            overlay_files = _read_overlay_manifest(private_dir)
            _remove_overlay(public_dir, template_source_dir, company_only_files, overlay_files)
            validate_directory(public_dir)
            verify_files = (
                [p for p in overlay_files if not (template_source_dir / p).exists()]
                if overlay_files
                else None
            )
            if not verify_public_export(template_source_dir, public_dir, verify_files):
                raise SystemExit('❌ Public export verification failed')
        except Exception:
            rollback_manager.rollback_to(rollback_id)
            raise
    return public_dir


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



