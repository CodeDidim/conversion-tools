from pathlib import Path
import argparse
import json
import subprocess
from urllib import request

from core.rollback import RollbackManager

import workflow as home

DEFAULT_CONFIG = Path('.workflow-config-company.yaml')
MAIN_CONFIG = Path('.workflow-config.yaml')

rollback_manager = RollbackManager(Path('.'))


def private_workflow(
    config_path: Path = DEFAULT_CONFIG,
    *,
    dry_run: bool = False,
) -> Path:
    return home.private_workflow(config_path, dry_run=dry_run)


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    """Load configuration using the shared loader."""
    return home.load_config(path)


def repo_is_public(owner: str, repo: str) -> bool:
    """Return True if the GitHub repo is public."""
    return home.repo_is_public(owner, repo)


def repo_status(cfg: dict) -> str:
    """Return 'public' or 'private' for the repo specified in cfg."""
    return home.repo_status(cfg)


def repo_status(cfg: dict) -> str:
    """Return 'public' or 'private' for the repo specified in cfg."""
    owner = (
        cfg.get("github.owner")
        or cfg.get("github", {}).get("owner")
        or cfg.get("owner")
    )
    repo = (
        cfg.get("github.repo")
        or cfg.get("github", {}).get("repo")
        or cfg.get("repo")
    )
    if not owner or not repo:
        raise SystemExit(
            "❌ github.owner and github.repo must be set in config\n"
            "\n"
            "Copy examples/.workflow-config-company.yaml.example, update owner/repo,"\
            " and place it as .workflow-config-company.yaml."
        )
    return "public" if repo_is_public(owner, repo) else "private"


def confirm(message: str) -> bool:
    resp = input(f"{message} [y/N]: ").strip().lower()
    return resp == "y"


def pull_repo(cfg: dict, force: bool = False) -> None:
    owner = (
        cfg.get("github.owner")
        or cfg.get("github", {}).get("owner")
        or cfg.get("owner")
    )
    repo = (
        cfg.get("github.repo")
        or cfg.get("github", {}).get("repo")
        or cfg.get("repo")
    )
    if not owner or not repo:
        raise SystemExit(
            "❌ github.owner and github.repo must be set in config\n"
            "\n"
            "Copy examples/.workflow-config-company.yaml.example, update owner/repo,"\
            " and place it as .workflow-config-company.yaml."
        )

    if not force:
        if not repo_is_public(owner, repo):
            raise SystemExit(
                "❌ Repository is private\n"
                "\n"
                "Make the GitHub repository public before pulling.\n"
                "You can unhide it using:\n"
                "    python scripts/github_visibility.py unhide\n"
                "Or run with --force to skip this check."
            )
        if not confirm("Repository is public. Continue with git pull?"):
            raise SystemExit(
                "❌ Pull cancelled\n"
                "Run 'workflow_company.py pull --force' to bypass confirmation."
            )

    subprocess.run(["git", "pull"], check=True)


def public_workflow(
    config_path: Path = DEFAULT_CONFIG,
    *,
    dry_run: bool = False,
) -> Path:
    return home.public_workflow(config_path, dry_run=dry_run)


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
    parser = argparse.ArgumentParser(description="Company workflow helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("private", help="Run private workflow")
    sub.add_parser("public", help="Run public workflow")
    roll = sub.add_parser("rollback", help="Manage rollbacks")
    roll.add_argument("--list", action="store_true")
    roll.add_argument("--to", type=str)
    roll.add_argument("--steps", type=int)
    roll.add_argument("--dry-run", action="store_true")
    pull_parser = sub.add_parser("pull", help="Git pull with safety checks")
    pull_parser.add_argument("--force", action="store_true", help="Skip safety checks")
    sub.add_parser("status", help="Show repository visibility")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Config file path")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making changes")
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
    elif args.command == "pull":
        ensure_config(MAIN_CONFIG)
        cfg = load_config(MAIN_CONFIG)
        pull_repo(cfg, force=args.force)
    elif args.command == "status":
        print(f"Using config file: {MAIN_CONFIG.resolve()}")
        ensure_config(MAIN_CONFIG)
        cfg = load_config(MAIN_CONFIG)
        vis = repo_status(cfg)
        print(f"Repository is {vis}")


if __name__ == "__main__":
    main()


