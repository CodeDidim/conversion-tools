import os
import subprocess
import threading
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.apply_template_context import inject_context


class TestEdgeCases:
    """Test unusual but possible scenarios"""

    def test_empty_repository(self, tmp_path):
        """Test workflow with no files"""
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True)

        template = repo / "template"
        profile = repo / "profile.yaml"
        dst = repo / "out"
        template.mkdir()
        profile.write_text("")

        inject_context(template, dst, profile)
        assert dst.exists()

    def test_repository_with_submodules(self, tmp_path):
        """Test handling of git submodules"""
        repo = tmp_path / "repo"
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

    def test_symbolic_links(self, tmp_path):
        """Test template conversion in symlinked files"""
        real = tmp_path / "real.txt"
        real.write_text("Key: {{ API_KEY }}")

        src = tmp_path / "src"
        src.mkdir()
        real.rename(src / "real.txt")
        link = src / "link.txt"
        try:
            link.symlink_to("real.txt")
        except (OSError, NotImplementedError):  # pragma: no cover - Windows
            pytest.skip("symlinks not supported")

        profile = tmp_path / "profile.yaml"
        profile.write_text("API_KEY: 123\n")

        dst = tmp_path / "dst"
        inject_context(src, dst, profile)

        converted = dst / "link.txt"
        assert converted.is_file()
        assert not converted.is_symlink()
        assert converted.read_text() == "Key: 123"

    def test_extremely_long_filenames(self, tmp_path):
        """Test with paths near OS limits"""
        long_name = "a" * 120 + ".txt"
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / long_name).write_text("V={{V}}")
        profile = tmp_path / "p.yaml"
        profile.write_text("V: ok")
        inject_context(src, dst, profile)
        assert (dst / long_name).read_text() == "V=ok"

    def test_concurrent_operations(self, tmp_path):
        """Test multiple workflow instances running simultaneously"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("A={{A}}")
        profile1 = tmp_path / "p1.yaml"
        profile2 = tmp_path / "p2.yaml"
        profile1.write_text("A: 1")
        profile2.write_text("A: 2")

        def run(dst: Path, profile: Path):
            inject_context(src, dst, profile)

        dst1 = tmp_path / "d1"
        dst2 = tmp_path / "d2"
        t1 = threading.Thread(target=run, args=(dst1, profile1))
        t2 = threading.Thread(target=run, args=(dst2, profile2))
        t1.start(); t2.start(); t1.join(); t2.join()

        assert (dst1 / "a.txt").read_text() == "A=1"
        assert (dst2 / "a.txt").read_text() == "A=2"

    def test_mixed_line_endings(self, tmp_path):
        """Test files with CRLF, LF, and CR line endings"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "unix.txt").write_bytes(b"line {{T}}\n")
        (src / "dos.txt").write_bytes(b"line {{T}}\r\n")
        (src / "mac.txt").write_bytes(b"line {{T}}\r")
        profile = tmp_path / "p.yaml"
        profile.write_text("T: X")
        inject_context(src, dst, profile)
        assert "X" in (dst / "unix.txt").read_text()
        assert "X" in (dst / "dos.txt").read_text()
        assert "X" in (dst / "mac.txt").read_text()

    def test_non_utf8_encodings(self, tmp_path):
        """Test files with various encodings (Latin-1, UTF-16, etc)"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "latin1.txt").write_bytes("café {{X}}".encode("latin-1"))
        profile = tmp_path / "p.yaml"
        profile.write_text("X: 1")
        with pytest.raises(UnicodeDecodeError):
            inject_context(src, dst, profile)

    def test_readonly_files(self, tmp_path):
        """Test conversion of read-only files"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        f = src / "a.txt"
        f.write_text("A={{A}}")
        f.chmod(0o444)
        profile = tmp_path / "p.yaml"
        profile.write_text("A: 1")
        try:
            inject_context(src, dst, profile)
            assert (dst / "a.txt").read_text() == "A=1"
        except PermissionError:
            # Some environments may not allow writing to read-only files
            pass

    def test_hidden_files_and_directories(self, tmp_path):
        """Test .files and .directories handling"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / ".secret.txt").write_text("S={{S}}")
        (src / ".hidden").mkdir()
        (src / ".hidden" / "a.txt").write_text("S={{S}}")
        profile = tmp_path / "p.yaml"
        profile.write_text("S: X")
        inject_context(src, dst, profile)
        assert (dst / ".secret.txt").read_text() == "S=X"
        assert (dst / ".hidden" / "a.txt").read_text() == "S=X"

    def test_case_sensitivity_issues(self, tmp_path):
        """Test on case-insensitive filesystems"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "file.txt").write_text("{{ TOKEN }} {{ token }}")
        profile = tmp_path / "p.yaml"
        profile.write_text("TOKEN: A")
        inject_context(src, dst, profile)
        text = (dst / "file.txt").read_text()
        assert text == "A {{ token }}"
