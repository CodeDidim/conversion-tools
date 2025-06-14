import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow


def test_validate_workflow_missing_config(tmp_path):
    cfg = tmp_path / "nope.yaml"
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok


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
        ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
        assert ok
        assert errors == []
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
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok


def test_validate_workflow_binary_placeholder(tmp_path):
    cfg = tmp_path / "c.yaml"
    template = tmp_path / "template"
    profile = tmp_path / "p.yaml"
    template.mkdir()
    (template / "data.bin").write_bytes(b"\x00{{X}}\x00")
    profile.write_text("X: 1\n")
    cfg.write_text(f"profile: '{profile}'\ntemplate: '{template}'\n")
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok
    assert any("binary" in e.lower() for e in errors)


def test_validate_workflow_nested_placeholder(tmp_path):
    cfg = tmp_path / "c.yaml"
    template = tmp_path / "template"
    profile = tmp_path / "p.yaml"
    template.mkdir()
    (template / "bad.txt").write_text("{{ {{X}} }}")
    profile.write_text("X: 1\n")
    cfg.write_text(f"profile: '{profile}'\ntemplate: '{template}'\n")
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok
    assert any("nested" in e.lower() for e in errors)
