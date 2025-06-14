import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.utils import sanitize_identifier, is_valid_identifier


def test_sanitize_identifier_examples():
    assert sanitize_identifier("ACME Corp") == "ACME_Corp"
    assert sanitize_identifier("123-test") == "test"
    assert sanitize_identifier("my-variable-name") == "my_variable_name"


def test_sanitize_identifier_keywords_and_empty():
    assert sanitize_identifier("class") == "var_class"
    assert sanitize_identifier("") == "unnamed"


def test_is_valid_identifier():
    assert is_valid_identifier("valid_name")
    assert not is_valid_identifier("123name")
    assert not is_valid_identifier("class")
    assert not is_valid_identifier("")
