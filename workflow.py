from pathlib import Path
import argparse

from core.rollback import RollbackManager
from scripts.apply_template_context import inject_context, load_profile
from scripts.revert_template_context import revert_context
from scripts.export_to_public import export_directory
from scripts.validate_public_repo import validate_directory

DEFAULT_CONFIG = Path('.workflow-config.yaml')

rollback_manager = RollbackManager(Path('.'))


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    return load_profile(path)


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
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.command == "private":
        private_workflow(args.config, dry_run=args.dry_run)
    elif args.command == "public":
        public_workflow(args.config, dry_run=args.dry_run)
    elif args.command == "rollback":
        _rollback_cli(args)


if __name__ == "__main__":
    main()



