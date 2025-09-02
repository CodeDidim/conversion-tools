from pathlib import Path
import os
import argparse
import json
from urllib import request

import yaml

DEFAULT_CONFIG = Path('.workflow-config.yaml')


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

    if not args.config.exists():
        raise SystemExit(f"\u274c Config file not found: {args.config}")

    cfg = load_config(args.config)

    gh = cfg.get("github")
    owner = None
    repo = None
    if isinstance(gh, dict):
        owner = gh.get("owner")
        repo = gh.get("repo")
    owner = owner or cfg.get("github.owner") or cfg.get("owner")
    repo = repo or cfg.get("github.repo") or cfg.get("repo")

    if not owner or not repo:
        raise SystemExit(
            "❌ github.owner and github.repo must be set in config\n"
            "\n"
            "Copy examples/.workflow-config.yaml.example, update owner/repo, and"\
            " place it as .workflow-config.yaml."
        )

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            "❌ GITHUB_TOKEN environment variable not found\n"
            "\n"
            "To fix this:\n"
            "1. Create a GitHub Personal Access Token:\n"
            "   https://github.com/settings/tokens\n"
            "2. Grant 'repo' scope\n"
            "3. Set the environment variable:\n"
            "   Linux/Mac: export GITHUB_TOKEN='ghp_your_token'\n"
            "   Windows:   set GITHUB_TOKEN=ghp_your_token\n"
            "   PowerShell: $env:GITHUB_TOKEN='ghp_your_token'\n"
        )

    make_private = args.command == "hide"
    set_visibility(owner, repo, make_private, token)


if __name__ == "__main__":
    main()

