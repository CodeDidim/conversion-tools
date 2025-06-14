import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow


def test_find_all_placeholders(tmp_path):
    template = tmp_path / "template"
    template.mkdir()
    (template / "a.txt").write_text("{{A}} {{ B }}")
    (template / "sub").mkdir()
    (template / "sub" / "b.py").write_text("x={{C}}")
    placeholders = workflow.find_all_placeholders(template)
    assert placeholders == {"A", "B", "C"}


def test_validate_profile_auto_append(tmp_path, monkeypatch):
    template = tmp_path / "template"
    template.mkdir()
    (template / "f.txt").write_text("{{A}} {{B}}")
    profile = tmp_path / "profile.yaml"
    profile.write_text("A: 1\n")
    monkeypatch.setenv("CONVERSION_AUTO_APPEND", "1")
    assert workflow.validate_profile(template, profile)
    text = profile.read_text()
    assert "B: TODO" in text
