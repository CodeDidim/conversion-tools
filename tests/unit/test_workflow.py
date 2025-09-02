import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow
import shutil
import pytest


def test_private_public_cycle(tmp_path):
    cfg = tmp_path / 'config.yaml'
    placeholder_values = tmp_path / 'profile.yaml'
    template_source_dir = tmp_path / 'template'
    company_only_files = tmp_path / 'overlay'
    working_directory = tmp_path / 'work'
    template_source_dir.mkdir()
    company_only_files.mkdir()
    (template_source_dir / 'a.txt').write_text('x={{X}}\n')
    (company_only_files / 'b.txt').write_text('y={{Y}}\n')
    placeholder_values.write_text('X: 1\nY: 2\n')
    cfg.write_text(
        f'placeholder_values: "{placeholder_values.as_posix()}"\n'
        f'company_only_files: "{company_only_files.as_posix()}"\n'
        f'working_directory: "{working_directory.as_posix()}"\n'
        f'template_source_dir: "{template_source_dir.as_posix()}"\n'
    )

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / 'a.txt').read_text() == 'x=1\n'
    assert (private_dir / 'b.txt').read_text() == 'y=2\n'

    public_dir = workflow.public_workflow(cfg)
    assert (public_dir / 'a.txt').exists()
    assert not (public_dir / 'b.txt').exists()


def test_private_public_dry_run(tmp_path):
    cfg = tmp_path / 'config.yaml'
    placeholder_values = tmp_path / 'profile.yaml'
    template_source_dir = tmp_path / 'template'
    company_only_files = tmp_path / 'overlay'
    working_directory = tmp_path / 'work'
    template_source_dir.mkdir()
    company_only_files.mkdir()
    (template_source_dir / 'a.txt').write_text('x={{X}}\n')
    placeholder_values.write_text('X: 1\n')
    cfg.write_text(
        f'placeholder_values: "{placeholder_values.as_posix()}"\n'
        f'company_only_files: "{company_only_files.as_posix()}"\n'
        f'working_directory: "{working_directory.as_posix()}"\n'
        f'template_source_dir: "{template_source_dir.as_posix()}"\n'
    )

    private_dir = workflow.private_workflow(cfg, dry_run=True)
    assert private_dir.exists() is False

    public_dir = workflow.public_workflow(cfg, dry_run=True)
    assert public_dir.exists() is False


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
    placeholder_values = tmp_path / 'p.yaml'
    template_source_dir = tmp_path / 'template'
    company_only_files = tmp_path / 'overlay'
    working_directory = tmp_path / 'work'
    template_source_dir.mkdir()
    company_only_files.mkdir()
    (template_source_dir / 'a.txt').write_text('orig={{A}}')
    (company_only_files / 'a.txt').write_text('private={{A}}')
    placeholder_values.write_text('A: 1')
    cfg.write_text(
        f'placeholder_values: "{placeholder_values.as_posix()}"\n'
        f'company_only_files: "{company_only_files.as_posix()}"\n'
        f'working_directory: "{working_directory.as_posix()}"\n'
        f'template_source_dir: "{template_source_dir.as_posix()}"\n'
    )

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / 'a.txt').read_text() == 'private=1'

    public_dir = workflow.public_workflow(cfg)
    assert (public_dir / 'a.txt').read_text() == 'orig={{A}}'


def test_overlay_manifest_used_when_overlay_missing(tmp_path, monkeypatch):
    cfg = tmp_path / 'c.yaml'
    placeholder_values = tmp_path / 'p.yaml'
    template_source_dir = tmp_path / 'template'
    company_only_files = tmp_path / 'overlay'
    working_directory = tmp_path / 'work'
    template_source_dir.mkdir()
    company_only_files.mkdir()
    (template_source_dir / 'base.txt').write_text('x={{X}}')
    (company_only_files / 'secret.txt').write_text('s={{S}}')
    placeholder_values.write_text('X: 1\nS: 2')
    cfg.write_text(
        f'placeholder_values: "{placeholder_values.as_posix()}"\n'
        f'company_only_files: "{company_only_files.as_posix()}"\n'
        f'working_directory: "{working_directory.as_posix()}"\n'
        f'template_source_dir: "{template_source_dir.as_posix()}"\n'
    )

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / 'secret.txt').exists()
    assert (private_dir / '.overlay_manifest').exists()

    # Remove overlay directory before running public workflow
    shutil.rmtree(company_only_files)

    captured = {}
    original_remove = workflow._remove_overlay

    def spy(public_dir, template_dir, company_only_files_dir, overlay_files=None):
        captured["files"] = overlay_files
        return original_remove(public_dir, template_dir, company_only_files_dir, overlay_files)

    monkeypatch.setattr(workflow, "_remove_overlay", spy)

    ver = {}

    def fake_verify(t_dir, e_dir, manifest=None):
        ver["manifest"] = manifest
        return True

    monkeypatch.setattr(workflow, "verify_public_export", fake_verify)

    public_dir = workflow.public_workflow(cfg)
    assert (public_dir / 'secret.txt').exists() is False
    assert captured.get("files") == [Path('secret.txt')]
    assert ver.get("manifest") == [Path('secret.txt')]


def test_public_workflow_runs_verification(tmp_path, monkeypatch):
    cfg = tmp_path / 'c.yaml'
    placeholder_values = tmp_path / 'p.yaml'
    template_source_dir = tmp_path / 'template'
    working_directory = tmp_path / 'work'
    template_source_dir.mkdir()
    (template_source_dir / 'a.txt').write_text('x={{X}}')
    placeholder_values.write_text('X: 1')
    cfg.write_text(
        f'placeholder_values: "{placeholder_values.as_posix()}"\n'
        f'working_directory: "{working_directory.as_posix()}"\n'
        f'template_source_dir: "{template_source_dir.as_posix()}"\n'
    )

    captured = {}

    def fake_verify(t_dir, e_dir, manifest=None):
        captured['args'] = (t_dir, e_dir, manifest)
        return True

    monkeypatch.setattr(workflow, 'verify_public_export', fake_verify)

    public_dir = workflow.public_workflow(cfg)

    assert captured['args'][0] == template_source_dir
    assert captured['args'][1] == public_dir
    assert captured['args'][2] is None


def test_public_workflow_verification_failure(tmp_path, monkeypatch):
    cfg = tmp_path / 'c.yaml'
    placeholder_values = tmp_path / 'p.yaml'
    template_source_dir = tmp_path / 'template'
    working_directory = tmp_path / 'work'
    template_source_dir.mkdir()
    (template_source_dir / 'a.txt').write_text('x={{X}}')
    placeholder_values.write_text('X: 1')
    cfg.write_text(
        f'placeholder_values: "{placeholder_values.as_posix()}"\n'
        f'working_directory: "{working_directory.as_posix()}"\n'
        f'template_source_dir: "{template_source_dir.as_posix()}"\n'
    )

    monkeypatch.setattr(workflow, 'verify_public_export', lambda *a, **k: False)

    workflow.private_workflow(cfg)

    with pytest.raises(SystemExit):
        workflow.public_workflow(cfg)

