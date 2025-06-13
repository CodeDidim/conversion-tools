import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.validate_public_repo import validate_directory


def test_validate_directory_passes(tmp_path):
    base = tmp_path / "export"
    base.mkdir()
    (base / "good.txt").write_text("nothing here\n")
    assert validate_directory(base)


def test_validate_directory_fails(tmp_path):
    base = tmp_path / "export"
    base.mkdir()
    (base / "bad.txt").write_text("contact me at secret@example.com\n")
    assert not validate_directory(base)


def test_validate_directory_detects_keys(tmp_path):
    base = tmp_path / "export"
    base.mkdir()
    (base / "key.txt").write_text("ssh-rsa AAAAB3Nza...\n")
    assert not validate_directory(base)
