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
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    gitignore = tmp_path / ".gitignore"
    template_source_dir.mkdir()
    (template_source_dir / "a.txt").write_text("x={{X}}")
    placeholder_values.write_text("X: 1\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
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
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    template_source_dir.mkdir()
    (template_source_dir / "a.txt").write_text("x={{X}}")
    placeholder_values.write_text("X: {{bad}}\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok


def test_validate_workflow_binary_placeholder(tmp_path):
    cfg = tmp_path / "c.yaml"
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    template_source_dir.mkdir()
    (template_source_dir / "data.bin").write_bytes(b"\x00{{X}}\x00")
    placeholder_values.write_text("X: 1\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok
    assert any("binary" in e.lower() for e in errors)


def test_validate_workflow_nested_placeholder(tmp_path):
    cfg = tmp_path / "c.yaml"
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    template_source_dir.mkdir()
    (template_source_dir / "bad.txt").write_text("{{ {{X}} }}")
    placeholder_values.write_text("X: 1\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok
    assert any("nested" in e.lower() for e in errors)


def test_validate_workflow_missing_key_locations(tmp_path):
    cfg = tmp_path / "c.yaml"
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    template_source_dir.mkdir()
    (template_source_dir / "a.txt").write_text("first={{ONE}}\nsecond={{TWO}}\n")
    placeholder_values.write_text("ONE: 1\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
    ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    assert not ok
    msg = ";".join(errors)
    assert "TWO" in msg
    assert str(template_source_dir / "a.txt") in msg
    assert ":2" in msg


def test_validate_workflow_identifier_error(tmp_path):
    cfg = tmp_path / "c.yaml"
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    gitignore = tmp_path / ".gitignore"
    template_source_dir.mkdir()
    (template_source_dir / "client.py").write_text(
        "class {{ COMPANY_NAME }}Client:\n    pass\n"
    )
    placeholder_values.write_text("COMPANY_NAME: ACME-Corp\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
    gitignore.write_text(".workflow-config.yaml\nprivate-overlay\n")
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    finally:
        os.chdir(cwd)
    assert not ok
    assert any("invalid identifier" in e for e in errors)


def test_validate_workflow_identifier_spaces_warning(tmp_path):
    cfg = tmp_path / "c.yaml"
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    gitignore = tmp_path / ".gitignore"
    template_source_dir.mkdir()
    (template_source_dir / "client.py").write_text(
        "class {{ COMPANY_NAME }}Client:\n    pass\n"
    )
    placeholder_values.write_text("COMPANY_NAME: ACME Corp\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
    gitignore.write_text(".workflow-config.yaml\nprivate-overlay\n")
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    finally:
        os.chdir(cwd)
    assert ok
    assert errors == []
    assert any("contains spaces" in w for w in warnings)


def test_validate_workflow_private_reference(tmp_path):
    cfg = tmp_path / "c.yaml"
    template_source_dir = tmp_path / "template"
    placeholder_values = tmp_path / "p.yaml"
    gitignore = tmp_path / ".gitignore"
    template_source_dir.mkdir()

    content = "Email: support@company.com\nOrg: MY_ORGANIZATION_NAME\n"
    (template_source_dir / "info.txt").write_text(content)
    placeholder_values.write_text("DUMMY: 1\n")
    cfg.write_text(
        f"placeholder_values: '{placeholder_values.as_posix()}'\n"
        f"template_source_dir: '{template_source_dir.as_posix()}'\n"
    )
    gitignore.write_text(".workflow-config.yaml\n")

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        ok, errors, warnings = workflow.validate_before_workflow(cfg, "private")
    finally:
        os.chdir(cwd)
    assert not ok

    msg = "\n".join(errors)
    assert "support@company.com" in msg
    assert "MY_ORGANIZATION_NAME" in msg
    assert str(template_source_dir / "info.txt") in msg
    assert ":1" in msg and ":2" in msg

