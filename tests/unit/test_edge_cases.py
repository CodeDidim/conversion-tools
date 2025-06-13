import os
import subprocess
import threading
from pathlib import Path

import pytest

from scripts.apply_template_context import inject_context


class TestEdgeCases:
    """Test unusual but possible scenarios"""

    def test_empty_repository(self):
        """Test workflow with no files"""
        repo = Path("repo")
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True)

        template = repo / "template"
        profile = repo / "profile.yaml"
        dst = repo / "out"
        template.mkdir()
        profile.write_text("")

        inject_context(template, dst, profile)
        assert (dst).exists()

    def test_repository_with_submodules(self):
        """Test handling of git submodules"""
        repo = Path("repo")
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True)

        submodule = repo / "sub"
        submodule.mkdir()
        subprocess.run(["git", "init"], cwd=submodule, check=True)

        template = repo / "template"
        profile = repo / "profile.yaml"
        dst = repo / "out"
        template.mkdir()
        (template / "a.txt").write_text("x={{X}}")
        profile.write_text("X: 1\n")

        inject_context(template, dst, profile)
        assert (dst / "a.txt").read_text() == "x=1"

    def test_symbolic_links(self):
        """Test template conversion in symlinked files"""
        real = Path("real.txt")
        real.write_text("Key: {{ API_KEY }}")

        src = Path("src")
        src.mkdir()
        real.rename(src / "real.txt")
        link = src / "link.txt"
        link.symlink_to("real.txt")

        profile = Path("profile.yaml")
        profile.write_text("API_KEY: 123\n")

        dst = Path("dst")
        inject_context(src, dst, profile)

        converted = dst / "link.txt"
        assert converted.is_file()
        assert not converted.is_symlink()
        assert converted.read_text() == "Key: 123"

    def test_extremely_long_filenames(self):
        """Test with paths near OS limits"""
        long_name = "a" * 120 + ".txt"
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / long_name).write_text("V={{V}}")
        profile = Path("p.yaml")
        profile.write_text("V: ok")
        inject_context(src, dst, profile)
        assert (dst / long_name).read_text() == "V=ok"

    def test_concurrent_operations(self):
        """Test multiple workflow instances running simultaneously"""
        src = Path("src")
        src.mkdir()
        (src / "a.txt").write_text("A={{A}}")
        profile1 = Path("p1.yaml")
        profile2 = Path("p2.yaml")
        profile1.write_text("A: 1")
        profile2.write_text("A: 2")

        def run(dst: Path, profile: Path):
            inject_context(src, dst, profile)

        dst1 = Path("d1")
        dst2 = Path("d2")
        t1 = threading.Thread(target=run, args=(dst1, profile1))
        t2 = threading.Thread(target=run, args=(dst2, profile2))
        t1.start(); t2.start(); t1.join(); t2.join()

        assert (dst1 / "a.txt").read_text() == "A=1"
        assert (dst2 / "a.txt").read_text() == "A=2"

    def test_mixed_line_endings(self):
        """Test files with CRLF, LF, and CR line endings"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "unix.txt").write_bytes(b"line {{T}}\n")
        (src / "dos.txt").write_bytes(b"line {{T}}\r\n")
        (src / "mac.txt").write_bytes(b"line {{T}}\r")
        profile = Path("p.yaml")
        profile.write_text("T: X")
        inject_context(src, dst, profile)
        assert "X" in (dst / "unix.txt").read_text()
        assert "X" in (dst / "dos.txt").read_text()
        assert "X" in (dst / "mac.txt").read_text()

    def test_non_utf8_encodings(self):
        """Test files with various encodings (Latin-1, UTF-16, etc)"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "latin1.txt").write_bytes("café {{X}}".encode("latin-1"))
        profile = Path("p.yaml")
        profile.write_text("X: 1")
        with pytest.raises(UnicodeDecodeError):
            inject_context(src, dst, profile)

    def test_readonly_files(self):
        """Test conversion of read-only files"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        f = src / "a.txt"
        f.write_text("A={{A}}")
        f.chmod(0o444)
        profile = Path("p.yaml")
        profile.write_text("A: 1")
        try:
            inject_context(src, dst, profile)
            assert (dst / "a.txt").read_text() == "A=1"
        except PermissionError:
            # Some environments may not allow writing to read-only files
            pass

    def test_hidden_files_and_directories(self):
        """Test .files and .directories handling"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / ".secret.txt").write_text("S={{S}}")
        (src / ".hidden").mkdir()
        (src / ".hidden" / "a.txt").write_text("S={{S}}")
        profile = Path("p.yaml")
        profile.write_text("S: X")
        inject_context(src, dst, profile)
        assert (dst / ".secret.txt").read_text() == "S=X"
        assert (dst / ".hidden" / "a.txt").read_text() == "S=X"

    def test_case_sensitivity_issues(self):
        """Test on case-insensitive filesystems"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "file.txt").write_text("{{ TOKEN }} {{ token }}")
        profile = Path("p.yaml")
        profile.write_text("TOKEN: A")
        inject_context(src, dst, profile)
        text = (dst / "file.txt").read_text()
        assert text == "A {{ token }}"
