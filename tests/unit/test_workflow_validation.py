import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow


def test_validate_workflow_missing_config(tmp_path):
    cfg = tmp_path / "nope.yaml"
    assert not workflow.validate_workflow_setup(cfg)


def test_validate_workflow_basic(tmp_path, monkeypatch):
    cfg = tmp_path / "c.yaml"
    template = tmp_path / "template"
    profile = tmp_path / "p.yaml"
    gitignore = tmp_path / ".gitignore"
    template.mkdir()
    (template / "a.txt").write_text("x={{X}}")
    profile.write_text("X: 1\n")
    cfg.write_text(f"profile: '{profile}'\ntemplate: '{template}'\n")
    gitignore.write_text(".workflow-config.yaml\n")
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        assert workflow.validate_workflow_setup(cfg)
    finally:
        os.chdir(cwd)


def test_validate_workflow_profile_error(tmp_path):
    cfg = tmp_path / "c.yaml"
    template = tmp_path / "template"
    profile = tmp_path / "p.yaml"
    template.mkdir()
    (template / "a.txt").write_text("x={{X}}")
    profile.write_text("X: {{bad}}\n")
    cfg.write_text(f"profile: '{profile}'\ntemplate: '{template}'\n")
    assert not workflow.validate_workflow_setup(cfg)
