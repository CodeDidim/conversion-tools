from pathlib import Path
import workflow as home

DEFAULT_CONFIG = Path('.workflow-config-company.yaml')


def private_workflow(config_path: Path = DEFAULT_CONFIG) -> Path:
    return home.private_workflow(config_path)


def public_workflow(config_path: Path = DEFAULT_CONFIG) -> Path:
    return home.public_workflow(config_path)


if __name__ == '__main__':
    private_workflow()
