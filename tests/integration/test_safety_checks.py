import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.validate_public_repo import validate_directory


def test_validation_detects_private(tmp_path):
    base = tmp_path / 'public'
    base.mkdir()
    (base / 'secret.txt').write_text('email@secret.com')
    assert not validate_directory(base)
