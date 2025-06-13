from pathlib import Path
import argparse
import sys
import subprocess
import json
from urllib import request
from typing import Optional

from core.rollback import RollbackManager
from scripts.apply_template_context import inject_context, load_profile
from scripts.revert_template_context import revert_context
from scripts.export_to_public import export_directory
from scripts.validate_public_repo import validate_directory
from scripts.manage_logs import cleanup_logs

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


def repo_status(cfg: dict) -> str:
    """Return 'public' or 'private' based on GitHub visibility."""

    owner = cfg.get("github.owner")
    repo = cfg.get("github.repo")
    github = cfg.get("github")
    if isinstance(github, dict):
        owner = owner or github.get("owner")
        repo = repo or github.get("repo")

    if not owner or not repo:
        raise SystemExit(
            "❌ github.owner and github.repo must be set in config\n"
            "\n"
            "Run 'workflow.py init' to generate a default configuration or copy\n"
            "examples/.workflow-config.yaml.example and edit owner/repo."
        )
    return "public" if repo_is_public(owner, repo) else "private"


def private_workflow(
    config_path: Path = DEFAULT_CONFIG,
    *,
    dry_run: bool = False,
) -> Path:
    cfg = load_config(config_path)
    temp_dir = Path(cfg.get('temp_dir', '.workflow-temp'))
    template = Path(cfg.get('template', 'template'))
    profile = Path(cfg.get('profile', 'scripts/config_profiles/company_profile.yaml'))
    overlay = Path(cfg.get('overlay_dir', 'private-overlay'))
    dst = temp_dir / 'private'
    rollback_id = None
    if not dry_run:
        rollback_id = rollback_manager.create_snapshot('to_private', cfg)
        try:
            inject_context(template, dst, profile, overlay)
        except Exception:
            rollback_manager.rollback_to(rollback_id)
            raise
    return dst


def public_workflow(
    config_path: Path = DEFAULT_CONFIG,
    *,
    dry_run: bool = False,
) -> Path:
    cfg = load_config(config_path)
    temp_dir = Path(cfg.get('temp_dir', '.workflow-temp'))
    profile = Path(cfg.get('profile', 'scripts/config_profiles/company_profile.yaml'))
    private_dir = temp_dir / 'private'
    public_dir = temp_dir / 'public'
    export_dir = temp_dir / 'export'
    rollback_id = None
    if not dry_run:
        rollback_id = rollback_manager.create_snapshot('to_public', cfg)
        try:
            revert_context(private_dir, public_dir, profile)
            export_directory(public_dir, export_dir)
            validate_directory(export_dir)
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

    if args.command == "private":
        private_workflow(args.config, dry_run=args.dry_run)
    elif args.command == "public":
        public_workflow(args.config, dry_run=args.dry_run)
    elif args.command == "rollback":
        _rollback_cli(args)
    elif args.command == "clean-logs":
        cleanup_logs(Path("log"), 30)
    elif args.command == "status":
        print(f"Using config file: {Path(args.config).resolve()}")

        cfg = load_config(args.config)
        vis = repo_status(cfg)
        print(f"Repository is {vis}")


if __name__ == "__main__":
    main()



