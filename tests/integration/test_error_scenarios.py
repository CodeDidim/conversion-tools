import sys
from pathlib import Path
import subprocess
import os
import shutil
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow
from scripts.validate_public_repo import validate_directory
from scripts.apply_template_context import inject_context


class TestErrorScenarios:
    """Test error handling and recovery"""


    def test_push_with_secrets_exposed(self, tmp_path):
        """Attempt to push code that still contains secrets"""
        base = tmp_path / "public"
        base.mkdir()
        (base / "file.txt").write_text("email@company.com")
        assert not validate_directory(base)

    def test_interrupted_conversion(self, tmp_path):
        """Simulate crash during private->public conversion"""
        cfg = tmp_path / "c.yaml"
        placeholder_values = tmp_path / "p.yaml"
        template_source_dir = tmp_path / "t"
        template_source_dir.mkdir()
        (template_source_dir / "a.txt").write_text("x={{X}}")
        placeholder_values.write_text("X: 1")
        cfg.write_text(
            f"placeholder_values: \"{placeholder_values.as_posix()}\"\n"
            f"template_source_dir: \"{template_source_dir.as_posix()}\"\n"
            f"working_directory: \"{tmp_path.as_posix()}\"\n"
        )
        workflow.private_workflow(cfg)

        def boom(*a, **k):
            raise RuntimeError("boom")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(shutil, "copytree", boom)
        with pytest.raises(RuntimeError):
            workflow.public_workflow(cfg)
        assert not (tmp_path / "public").exists()
        monkeypatch.undo()

    def test_git_conflicts_during_conversion(self, tmp_path):
        """Create git conflicts then attempt conversion"""
        cfg = tmp_path / "c.yaml"
        placeholder_values = tmp_path / "p.yaml"
        template_source_dir = tmp_path / "t"
        template_source_dir.mkdir()
        (template_source_dir / "a.txt").write_text("x={{X}}")
        placeholder_values.write_text("X: 1")
        cfg.write_text(
            f"placeholder_values: \"{placeholder_values.as_posix()}\"\n"
            f"template_source_dir: \"{template_source_dir.as_posix()}\"\n"
            f"working_directory: \"{tmp_path.as_posix()}\"\n"
        )
        workflow.private_workflow(cfg)

        def conflict(*a, **k):
            raise RuntimeError("conflict")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(workflow, "verify_public_export", conflict)
        with pytest.raises(RuntimeError):
            workflow.public_workflow(cfg)
        monkeypatch.undo()

    def test_missing_config_file(self):
        """Test behavior when config files are missing"""
        with pytest.raises(SystemExit):
            workflow.private_workflow(Path("missing.yaml"))

    def test_missing_template_files(self, tmp_path):
        """Workflow fails when template directory is absent"""
        cfg = tmp_path / "config.yaml"
        placeholder_values = tmp_path / "profile.yaml"
        placeholder_values.write_text("X: 1\n")
        missing = tmp_path / "missing"
        cfg.write_text(
            f"placeholder_values: '{placeholder_values.as_posix()}'\n"
            f"template_source_dir: '{missing.as_posix()}'\n"
            f"working_directory: '{tmp_path.as_posix()}'\n"
        )
        with pytest.raises(SystemExit):
            workflow.private_workflow(cfg)

    def test_corrupted_profile_yaml(self, tmp_path):
        """Test handling of malformed YAML profiles"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "a.txt").write_text("v={{A}}")
        placeholder_values = tmp_path / "p.yaml"
        placeholder_values.write_text("A: 1\n: bad")
        with pytest.raises(ValueError):
            inject_context(src, dst, placeholder_values)

    def test_network_timeout_scenarios(self, tmp_path):
        """Test timeouts during git operations"""
        cfg = tmp_path / "c.yaml"
        placeholder_values = tmp_path / "p.yaml"
        template_source_dir = tmp_path / "t"
        template_source_dir.mkdir()
        (template_source_dir / "a.txt").write_text("x={{X}}")
        placeholder_values.write_text("X: 1")
        cfg.write_text(
            f"placeholder_values: \"{placeholder_values.as_posix()}\"\n"
            f"template_source_dir: \"{template_source_dir.as_posix()}\"\n"
            f"working_directory: \"{tmp_path.as_posix()}\"\n"
        )

        orig_run = subprocess.run

        def fake_run(args, **kw):
            if args[0] == "git":
                raise subprocess.TimeoutExpired(args, 1)
            return orig_run(args, **kw)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(subprocess, "run", fake_run)
        workflow.private_workflow(cfg)
        monkeypatch.undo()

    def test_insufficient_permissions(self, tmp_path):
        """Test handling of permission errors"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("x={{X}}")
        placeholder_values = tmp_path / "p.yaml"
        placeholder_values.write_text("X: 1")
        dst = tmp_path / "out"

        orig_write_text = Path.write_text

        def deny(self, *a, **k):
            if self.suffix == ".txt" and self.name == "a.txt":
                raise PermissionError("read-only")
            return orig_write_text(self, *a, **k)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(Path, "write_text", deny)
        with pytest.raises(PermissionError):
            inject_context(src, dst, placeholder_values)
        monkeypatch.undo()

    def test_disk_space_exhaustion(self, tmp_path):
        """Test behavior when disk space runs out mid-operation"""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "a.txt").write_text("x={{X}}")
        placeholder_values = tmp_path / "p.yaml"
        placeholder_values.write_text("X: 1")

        import errno

        orig_write_text = Path.write_text

        def fail(self, *a, **kw):
            if self.suffix == ".txt":
                raise OSError(errno.ENOSPC, "no space")
            return orig_write_text(self, *a, **kw)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(Path, "write_text", fail)
        with pytest.raises(OSError):
            inject_context(src, dst, placeholder_values)
        monkeypatch.undo()
