import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow


def test_find_all_placeholders(tmp_path):
    template = tmp_path / "template"
    template.mkdir()
    (template / "a.txt").write_text("{{ALPHA}} {{ BETA }}")
    (template / "sub").mkdir()
    (template / "sub" / "b.py").write_text("x={{GAMMA}}")
    placeholders = workflow.find_all_placeholders(template)
    assert placeholders == {"ALPHA", "BETA", "GAMMA"}


def test_validate_profile_auto_append(tmp_path, monkeypatch):
    template = tmp_path / "template"
    template.mkdir()
    (template / "f.txt").write_text("{{FOO}} {{BAR}}")
    profile = tmp_path / "profile.yaml"
    profile.write_text("FOO: 1\n")
    monkeypatch.setenv("CONVERSION_AUTO_APPEND", "1")
    assert workflow.validate_profile(template, profile)
    text = profile.read_text()
    assert "BAR: TODO" in text


def test_is_valid_placeholder():
    assert workflow.is_valid_placeholder("API_KEY")
    assert not workflow.is_valid_placeholder("and")
    assert not workflow.is_valid_placeholder("a")
    assert not workflow.is_valid_placeholder("token")
    assert not workflow.is_valid_placeholder("TEST_VAL")
    assert not workflow.is_valid_placeholder("BAD KEY")


def test_validate_profile_with_ignore(tmp_path, monkeypatch):
    template = tmp_path / "template"
    template.mkdir()
    (template / "a.txt").write_text("{{API_ENDPOINT}} {{TOKEN}} {{EMPTY_VALUE}} {{LEGACY_TOKEN}} {{and}}")
    (template / ".placeholderignore").write_text("LEGACY_TOKEN\n")
    profile = tmp_path / "profile.yaml"
    profile.write_text("API_ENDPOINT: x\nignore_placeholders: LEGACY_TOKEN\n")
    monkeypatch.setenv("CONVERSION_AUTO_APPEND", "1")
    assert workflow.validate_profile(template, profile)
    lines = [l.split(":")[0] for l in profile.read_text().splitlines() if ":" in l]
    assert "TOKEN" not in lines
    assert "EMPTY_VALUE" not in lines
    assert "and" not in lines

