import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.export_to_public import export_directory


def test_export_directory_cleans_and_copies(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    # Create a Python file with lines that should be removed
    py_file = src / "file.py"
    py_file.write_text("hello\nYourCompany secret\nworld\n")

    # Create a text file that should not be cleaned
    txt_file = src / "file.txt"
    txt_file.write_text("private @company.com\n")

    # Create nested YAML file
    nested_dir = src / "nested"
    nested_dir.mkdir()
    yaml_file = nested_dir / "config.yaml"
    yaml_file.write_text("key: value\nMY_ORGANIZATION_NAME\n")

    export_directory(src, dst)

    # Python file cleaned
    py_lines = (dst / "file.py").read_text().splitlines()
    assert py_lines == ["hello", "world"]

    # Text file cleaned
    assert (dst / "file.txt").read_text() == ""

    # Nested yaml cleaned
    yaml_lines = (dst / "nested" / "config.yaml").read_text().splitlines()
    assert yaml_lines == ["key: value"]

