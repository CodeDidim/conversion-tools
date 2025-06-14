import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow
import shutil


def test_private_public_cycle(tmp_path):
    cfg = tmp_path / 'config.yaml'
    profile = tmp_path / 'profile.yaml'
    template = tmp_path / 'template'
    overlay = tmp_path / 'overlay'
    work = tmp_path / 'work'
    template.mkdir()
    overlay.mkdir()
    (template / 'a.txt').write_text('x={{X}}\n')
    (overlay / 'b.txt').write_text('y={{Y}}\n')
    profile.write_text('X: 1\nY: 2\n')
    cfg.write_text(f'profile: "{profile}"\noverlay_dir: "{overlay}"\ntemp_dir: "{work}"\ntemplate: "{template}"\n')

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / 'a.txt').read_text() == 'x=1\n'
    assert (private_dir / 'b.txt').read_text() == 'y=2\n'

    export_dir = workflow.public_workflow(cfg)
    assert (export_dir / 'a.txt').exists()
    assert not (export_dir / 'b.txt').exists()


def test_private_public_dry_run(tmp_path):
    cfg = tmp_path / 'config.yaml'
    profile = tmp_path / 'profile.yaml'
    template = tmp_path / 'template'
    overlay = tmp_path / 'overlay'
    work = tmp_path / 'work'
    template.mkdir()
    overlay.mkdir()
    (template / 'a.txt').write_text('x={{X}}\n')
    profile.write_text('X: 1\n')
    cfg.write_text(
        f'profile: "{profile}"\noverlay_dir: "{overlay}"\ntemp_dir: "{work}"\n'
        f'template: "{template}"\n'
    )

    private_dir = workflow.private_workflow(cfg, dry_run=True)
    assert private_dir.exists() is False

    export_dir = workflow.public_workflow(cfg, dry_run=True)
    assert export_dir.exists() is False


def test_repo_status(monkeypatch):
    cfg = {"github.owner": "o", "github.repo": "r"}

    monkeypatch.setattr(workflow, "repo_is_public", lambda o, r: True)
    assert workflow.repo_status(cfg) == "public"

    monkeypatch.setattr(workflow, "repo_is_public", lambda o, r: False)
    assert workflow.repo_status(cfg) == "private"

def test_repo_status_nested(monkeypatch):
    cfg = {"github": {"owner": "o", "repo": "r"}}

    monkeypatch.setattr(workflow, "repo_is_public", lambda o, r: True)
    assert workflow.repo_status(cfg) == "public"


def test_overlay_override_removed(tmp_path):
    cfg = tmp_path / 'c.yaml'
    profile = tmp_path / 'p.yaml'
    template = tmp_path / 'template'
    overlay = tmp_path / 'overlay'
    work = tmp_path / 'work'
    template.mkdir()
    overlay.mkdir()
    (template / 'a.txt').write_text('orig={{A}}')
    (overlay / 'a.txt').write_text('private={{A}}')
    profile.write_text('A: 1')
    cfg.write_text(
        f'profile: "{profile}"\noverlay_dir: "{overlay}"\ntemp_dir: "{work}"\n'
        f'template: "{template}"\n'
    )

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / 'a.txt').read_text() == 'private=1'

    export_dir = workflow.public_workflow(cfg)
    assert (export_dir / 'a.txt').read_text() == 'orig={{A}}'


def test_overlay_manifest_used_when_overlay_missing(tmp_path, monkeypatch):
    cfg = tmp_path / 'c.yaml'
    profile = tmp_path / 'p.yaml'
    template = tmp_path / 'template'
    overlay = tmp_path / 'overlay'
    work = tmp_path / 'work'
    template.mkdir()
    overlay.mkdir()
    (template / 'base.txt').write_text('x={{X}}')
    (overlay / 'secret.txt').write_text('s={{S}}')
    profile.write_text('X: 1\nS: 2')
    cfg.write_text(
        f'profile: "{profile}"\noverlay_dir: "{overlay}"\ntemp_dir: "{work}"\n'
        f'template: "{template}"\n'
    )

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / 'secret.txt').exists()
    assert (private_dir / '.overlay_manifest').exists()

    # Remove overlay directory before running public workflow
    shutil.rmtree(overlay)

    captured = {}
    original_remove = workflow._remove_overlay

    def spy(public_dir, template_dir, overlay_dir, overlay_files=None):
        captured["files"] = overlay_files
        return original_remove(public_dir, template_dir, overlay_dir, overlay_files)

    monkeypatch.setattr(workflow, "_remove_overlay", spy)

    export_dir = workflow.public_workflow(cfg)
    assert (export_dir / 'secret.txt').exists() is False
    assert captured.get("files") == [Path('secret.txt')]

