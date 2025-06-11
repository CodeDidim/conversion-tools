import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.apply_template_context import inject_context
from scripts.revert_template_context import revert_context


def test_roundtrip_revert(tmp_path):
    generic = tmp_path / "generic"
    private = tmp_path / "private"
    public = tmp_path / "public"
    generic.mkdir()

    (generic / "app.py").write_text("user={{ USER }}\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("USER: admin\n")

    inject_context(generic, private, profile)
    assert (private / "app.py").read_text() == "user=admin\n"

    revert_context(private, public, profile)
    assert (public / "app.py").read_text() == "user={{ USER }}\n"


def test_no_partial_word_replacement(tmp_path):
    private = tmp_path / "private"
    public = tmp_path / "public"
    private.mkdir()

    (private / "app.md").write_text("admin badmington\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("USER: admin\n")

    revert_context(private, public, profile)
    assert (public / "app.md").read_text() == "{{ USER }} badmington\n"
