from pathlib import Path
import os
import pytest

from scripts.apply_template_context import inject_context


class TestTemplateConversions:
    """Test template conversion edge cases"""

    def test_nested_placeholders(self):
        """Test: {{ {{ NESTED }} }}"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "file.txt").write_text("value={{ {{ NESTED }} }}")
        profile = Path("p.yaml")
        profile.write_text("NESTED: DONE")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "value={{ DONE }}"

    def test_partial_placeholder_matches(self):
        """Test: prefix{{ KEY }}suffix and adjacent placeholders"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "file.txt").write_text("pre{{ KEY }}post{{ KEY }}{{ KEY }}")
        profile = Path("p.yaml")
        profile.write_text("KEY: X")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "preXpostXX"

    def test_placeholder_in_different_contexts(self):
        """Test placeholders in various file contexts"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "code.py").write_text("API='{{ KEY }}'\n# {{ KEY }}")
        (src / "config.yaml").write_text("val: {{ KEY }}")
        profile = Path("p.yaml")
        profile.write_text("KEY: token")
        inject_context(src, dst, profile)
        assert "token" in (dst / "code.py").read_text()
        assert "token" in (dst / "config.yaml").read_text()

    def test_special_characters_in_values(self):
        """Test conversion with special characters"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "file.txt").write_text("x={{ KEY }}")
        profile = Path("p.yaml")
        profile.write_text("KEY: 'sp$\"c'\n")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "x=sp$\"c"

    def test_large_file_conversions(self):
        """Test performance with large files (>10MB)"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        big = src / "big.txt"
        chunk = ("data {{K}}\n" * 1000)
        big.write_text(chunk * 20)
        profile = Path("p.yaml")
        profile.write_text("K: v")
        inject_context(src, dst, profile)
        assert "v" in (dst / "big.txt").read_text()

    def test_binary_file_handling(self):
        """Ensure binary files are not corrupted"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        data = b"\x00\x01{{TOKEN}}\x02"
        (src / "file.bin").write_bytes(data)
        profile = Path("p.yaml")
        profile.write_text("TOKEN: value")
        inject_context(src, dst, profile)
        assert (dst / "file.bin").read_bytes() == data

    def test_circular_reference_prevention(self):
        """Value contains the placeholder itself"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "file.txt").write_text("A={{ A }}")
        profile = Path("p.yaml")
        profile.write_text("A: {{ A }}-done")
        inject_context(src, dst, profile)
        assert (dst / "file.txt").read_text() == "A={{ A }}-done"
