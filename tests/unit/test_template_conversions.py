from pathlib import Path
import os
import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.apply_template_context import inject_context


class TestTemplateConversions:
    """Test template conversion edge cases"""

    def test_nested_placeholders(self, tmp_path):
        """Test: {{ {{ NESTED }} }}"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "file.txt").write_text("value={{ {{ NESTED }} }}")
        profile = tmp_path / "p.yaml"
        profile.write_text("NESTED: DONE")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "value={{ DONE }}"

    def test_partial_placeholder_matches(self, tmp_path):
        """Test: prefix{{ KEY }}suffix and adjacent placeholders"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "file.txt").write_text("pre{{ KEY }}post{{ KEY }}{{ KEY }}")
        profile = tmp_path / "p.yaml"
        profile.write_text("KEY: X")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "preXpostXX"

    def test_placeholder_in_different_contexts(self, tmp_path):
        """Test placeholders in various file contexts"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "code.py").write_text("API='{{ KEY }}'\n# {{ KEY }}")
        (src / "config.yaml").write_text("val: {{ KEY }}")
        profile = tmp_path / "p.yaml"
        profile.write_text("KEY: token")
        inject_context(src, dst, profile)
        assert "token" in (dst / "code.py").read_text()
        assert "token" in (dst / "config.yaml").read_text()

    def test_special_characters_in_values(self, tmp_path):
        """Test conversion with special characters"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "file.txt").write_text("x={{ KEY }}")
        profile = tmp_path / "p.yaml"
        profile.write_text("KEY: 'sp$\"c'\n")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "x=sp$\"c"

    def test_large_file_conversions(self, tmp_path):
        """Test performance with large files (>10MB)"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        big = src / "big.txt"
        chunk = ("data {{K}}\n" * 1000)
        big.write_text(chunk * 20)
        profile = tmp_path / "p.yaml"
        profile.write_text("K: v")
        inject_context(src, dst, profile)
        assert "v" in (dst / "big.txt").read_text()

    def test_binary_file_handling(self, tmp_path):
        """Ensure binary files are not corrupted"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        data = b"\x00\x01{{TOKEN}}\x02"
        (src / "file.bin").write_bytes(data)
        profile = tmp_path / "p.yaml"
        profile.write_text("TOKEN: value")
        inject_context(src, dst, profile)
        assert (dst / "file.bin").read_bytes() == data

    def test_binary_detection_by_extension(self, tmp_path):
        """Files with known binary extensions are skipped"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        data = b"{{TOKEN}}"
        (src / "program.exe").write_bytes(data)
        profile = tmp_path / "p.yaml"
        profile.write_text("TOKEN: replaced")
        inject_context(src, dst, profile)
        assert (dst / "program.exe").read_bytes() == data

    def test_binary_detection_by_content(self, tmp_path):
        """Binary content in text extension is not modified"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        data = b"\x00\x01{{TOKEN}}\x02"
        (src / "weird.txt").write_bytes(data)
        profile = tmp_path / "p.yaml"
        profile.write_text("TOKEN: replaced")
        inject_context(src, dst, profile)
        assert (dst / "weird.txt").read_bytes() == data

    def test_circular_reference_prevention(self, tmp_path):
        """Value contains the placeholder itself"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "file.txt").write_text("A={{ A }}")
        profile = tmp_path / "p.yaml"
        profile.write_text("A: '{{ A }}-done'")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "A={{ A }}-done"

    def test_placeholders_in_class_and_function_names(self, tmp_path):
        """Placeholders can appear in Python identifiers"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        (src / "app.py").write_text(
            "class {{ CLASS_NAME }}:\n"
            "    def {{ FUNC_NAME }}(self):\n"
            "        return '{{ DOMAIN }}'\n"
        )

        profile = tmp_path / "profile.yaml"
        profile.write_text(
            "CLASS_NAME: Service\n"
            "FUNC_NAME: run\n"
            "DOMAIN: internal.example.com\n"
        )

        inject_context(src, dst, profile)

        text = (dst / "app.py").read_text()
        assert "class Service" in text
        assert "def run" in text
        assert "internal.example.com" in text

    def test_complex_url_transformation(self, tmp_path):
        """Complex URLs with multiple placeholders"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        (src / "url.txt").write_text(
            "https://{{ DOMAIN }}/api/{{ VERSION }}?token={{ TOKEN }}#ref"
        )

        profile = tmp_path / "profile.yaml"
        profile.write_text(
            "DOMAIN: example.com\n"
            "VERSION: v1\n"
            "TOKEN: abc123\n"
        )

        inject_context(src, dst, profile)

        result = (dst / "url.txt").read_text()
        assert "example.com" in result
        assert "v1" in result
        assert "abc123" in result
