import sys
from pathlib import Path
import subprocess
import os
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow
import workflow_company
from scripts.validate_public_repo import validate_directory
from scripts.apply_template_context import inject_context


class TestErrorScenarios:
    """Test error handling and recovery"""

    def test_pull_while_private(self):
        """Attempt to pull at company while repo is private"""
        cfg = {"github.owner": "o", "github.repo": "r"}

        def fake_public(o, r):
            return False

        def fake_confirm(msg):
            return False

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(workflow_company, "repo_is_public", fake_public)
        monkeypatch.setattr(workflow_company, "confirm", fake_confirm)

        with pytest.raises(SystemExit):
            workflow_company.pull_repo(cfg)
        monkeypatch.undo()

    def test_push_with_secrets_exposed(self):
        """Attempt to push code that still contains secrets"""
        base = Path("export")
        base.mkdir()
        (base / "file.txt").write_text("email@company.com")
        assert not validate_directory(base)

    def test_interrupted_conversion(self):
        """Simulate crash during private->public conversion"""
        cfg = Path("c.yaml")
        profile = Path("p.yaml")
        template = Path("t")
        template.mkdir()
        (template / "a.txt").write_text("x={{X}}")
        profile.write_text("X: 1")
        cfg.write_text(
            f"profile: \"{profile}\"\ntemplate: \"{template}\"\ntemp_dir: \"work\"\n"
        )
        workflow.private_workflow(cfg)

        def boom(*a, **k):
            raise RuntimeError("boom")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(workflow, "revert_context", boom)
        with pytest.raises(RuntimeError):
            workflow.public_workflow(cfg)
        assert not Path("work/public").exists()
        monkeypatch.undo()

    def test_git_conflicts_during_conversion(self):
        """Create git conflicts then attempt conversion"""
        cfg = Path("c.yaml")
        profile = Path("p.yaml")
        template = Path("t")
        template.mkdir()
        (template / "a.txt").write_text("x={{X}}")
        profile.write_text("X: 1")
        cfg.write_text(
            f"profile: \"{profile}\"\ntemplate: \"{template}\"\ntemp_dir: \"work\"\n"
        )
        workflow.private_workflow(cfg)

        def conflict(*a, **k):
            raise RuntimeError("conflict")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(workflow, "export_directory", conflict)
        with pytest.raises(RuntimeError):
            workflow.public_workflow(cfg)
        monkeypatch.undo()

    def test_missing_config_file(self):
        """Test behavior when config files are missing"""
        with pytest.raises(FileNotFoundError):
            workflow.private_workflow(Path("missing.yaml"))

    def test_corrupted_profile_yaml(self):
        """Test handling of malformed YAML profiles"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "a.txt").write_text("v={{A}}")
        profile = Path("p.yaml")
        profile.write_text("A: 1\n: bad")
        inject_context(src, dst, profile)
        assert (dst / "a.txt").read_text() == "v=1"

    def test_network_timeout_scenarios(self):
        """Test timeouts during git operations"""
        cfg = Path("c.yaml")
        profile = Path("p.yaml")
        template = Path("t")
        template.mkdir()
        (template / "a.txt").write_text("x={{X}}")
        profile.write_text("X: 1")
        cfg.write_text(
            f"profile: \"{profile}\"\ntemplate: \"{template}\"\ntemp_dir: \"work\"\n"
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

    def test_insufficient_permissions(self):
        """Test handling of permission errors"""
        src = Path("src")
        src.mkdir()
        (src / "a.txt").write_text("x={{X}}")
        profile = Path("p.yaml")
        profile.write_text("X: 1")
        dst = Path("out")

        orig_write_text = Path.write_text

        def deny(self, *a, **k):
            if self.suffix == ".txt" and self.name == "a.txt":
                raise PermissionError("read-only")
            return orig_write_text(self, *a, **k)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(Path, "write_text", deny)
        with pytest.raises(PermissionError):
            inject_context(src, dst, profile)
        monkeypatch.undo()

    def test_disk_space_exhaustion(self):
        """Test behavior when disk space runs out mid-operation"""
        src = Path("src")
        dst = Path("dst")
        src.mkdir()
        (src / "a.txt").write_text("x={{X}}")
        profile = Path("p.yaml")
        profile.write_text("X: 1")

        import errno

        orig_write_text = Path.write_text

        def fail(self, *a, **kw):
            if self.suffix == ".txt":
                raise OSError(errno.ENOSPC, "no space")
            return orig_write_text(self, *a, **kw)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(Path, "write_text", fail)
        with pytest.raises(OSError):
            inject_context(src, dst, profile)
        monkeypatch.undo()
