from pathlib import Path
from scripts.apply_template_context import inject_context, load_profile
from scripts.revert_template_context import revert_context
from scripts.export_to_public import export_directory
from scripts.validate_public_repo import validate_directory

DEFAULT_CONFIG = Path('.workflow-config.yaml')


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    return load_profile(path)


def private_workflow(config_path: Path = DEFAULT_CONFIG) -> Path:
    cfg = load_config(config_path)
    temp_dir = Path(cfg.get('temp_dir', '.workflow-temp'))
    template = Path(cfg.get('template', 'template'))
    profile = Path(cfg.get('profile', 'scripts/config_profiles/company_profile.yaml'))
    overlay = Path(cfg.get('overlay_dir', 'private-overlay'))
    dst = temp_dir / 'private'
    inject_context(template, dst, profile, overlay)
    return dst


def public_workflow(config_path: Path = DEFAULT_CONFIG) -> Path:
    cfg = load_config(config_path)
    temp_dir = Path(cfg.get('temp_dir', '.workflow-temp'))
    profile = Path(cfg.get('profile', 'scripts/config_profiles/company_profile.yaml'))
    private_dir = temp_dir / 'private'
    public_dir = temp_dir / 'public'
    revert_context(private_dir, public_dir, profile)
    export_dir = temp_dir / 'export'
    export_directory(public_dir, export_dir)
    validate_directory(export_dir)
    return export_dir


if __name__ == '__main__':
    private_workflow()
