from pathlib import Path
import os
import argparse
import json
from urllib import request

from scripts.apply_template_context import load_profile

DEFAULT_CONFIG = Path('.workflow-config.yaml')


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    return load_profile(path)


def set_visibility(owner: str, repo: str, make_private: bool, token: str) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = json.dumps({"private": make_private}).encode()
    req = request.Request(url, data=data, method="PATCH")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    request.urlopen(req)


def main() -> None:
    parser = argparse.ArgumentParser(description="Toggle GitHub repository visibility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("hide", help="Set repository private")
    sub.add_parser("unhide", help="Set repository public")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Config file path")
    args = parser.parse_args()

    cfg = load_config(args.config)
    gh = cfg.get("github", {})
    owner = gh.get("owner")
    repo = gh.get("repo")
    if not owner or not repo:
        raise SystemExit("github.owner and github.repo must be set in config")

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN environment variable required")

    make_private = args.command == "hide"
    set_visibility(owner, repo, make_private, token)


if __name__ == "__main__":
    main()

