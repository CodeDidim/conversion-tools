import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.verify_public_export import verify_public_export
from scripts.export_to_public import export_directory
from core.constants import KEYWORDS


def test_verify_export_simple(tmp_path):
    template = tmp_path / "template"
    export = tmp_path / "export"
    template.mkdir()
    (template / "a.txt").write_text("hello\n")
    export_directory(template, export)
    assert verify_public_export(template, export)


def test_verify_export_overlay_error(tmp_path):
    template = tmp_path / "template"
    export = tmp_path / "export"
    template.mkdir()
    (template / "a.txt").write_text("hello\n")
    export.mkdir()
    (export / "private.txt").write_text("secret\n")
    overlay = [Path("private.txt")]
    assert not verify_public_export(template, export, overlay)


def test_verify_export_mismatch(tmp_path):
    template = tmp_path / "template"
    export = tmp_path / "export"
    template.mkdir()
    (template / "a.txt").write_text("hello\n")
    export.mkdir()
    (export / "a.txt").write_text("oops\n")
    assert not verify_public_export(template, export)


def test_verify_export_cleaned_lines(tmp_path):
    template = tmp_path / "template"
    export = tmp_path / "export"
    template.mkdir()
    line = f"hidden {KEYWORDS[0]} text\n"
    (template / "readme.md").write_text("ok\n" + line + "end\n")
    export_directory(template, export)
    assert verify_public_export(template, export)
