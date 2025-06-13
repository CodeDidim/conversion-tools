from pathlib import Path
import argparse
import json
import subprocess
from urllib import request

import workflow as home

DEFAULT_CONFIG = Path('.workflow-config-company.yaml')
MAIN_CONFIG = Path('.workflow-config.yaml')


def private_workflow(config_path: Path = DEFAULT_CONFIG) -> Path:
    return home.private_workflow(config_path)


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    """Load configuration using the shared loader."""
    return home.load_config(path)


def repo_is_public(owner: str, repo: str) -> bool:
    """Return True if the GitHub repo is public."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = request.Request(url, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    with request.urlopen(req) as resp:
        data = json.load(resp)
    return not data.get("private", True)


def confirm(message: str) -> bool:
    resp = input(f"{message} [y/N]: ").strip().lower()
    return resp == "y"


def pull_repo(cfg: dict, force: bool = False) -> None:
    owner = cfg.get("github.owner")
    repo = cfg.get("github.repo")
    if not owner or not repo:
        raise SystemExit("github.owner and github.repo must be set in config")

    if not force:
        if not repo_is_public(owner, repo):
            raise SystemExit(
                "Repository is private. Please make it public using your phone"
            )
        if not confirm("Repository is public. Continue with git pull?"):
            raise SystemExit("Pull cancelled")

    subprocess.run(["git", "pull"], check=True)


def public_workflow(config_path: Path = DEFAULT_CONFIG) -> Path:
    return home.public_workflow(config_path)



def main() -> None:
    parser = argparse.ArgumentParser(description="Company workflow helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("private", help="Run private workflow")
    sub.add_parser("public", help="Run public workflow")
    pull_parser = sub.add_parser("pull", help="Git pull with safety checks")
    pull_parser.add_argument("--force", action="store_true", help="Skip safety checks")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Config file path")
    args = parser.parse_args()

    if args.command == "private":
        private_workflow(args.config)
    elif args.command == "public":
        public_workflow(args.config)
    elif args.command == "pull":
        cfg = load_config(MAIN_CONFIG)
        pull_repo(cfg, force=args.force)


if __name__ == "__main__":
    main()


