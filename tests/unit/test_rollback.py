import subprocess
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.rollback import RollbackManager


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)


def commit_file(path: Path, name: str, content: str, message: str) -> None:
    file = path / name
    file.write_text(content)
    subprocess.run(["git", "add", name], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=path, check=True)


def test_rollback_after_successful_conversion(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    commit_file(repo, "a.txt", "1", "init")

    rm = RollbackManager(repo)
    snap = rm.create_snapshot("op")

    commit_file(repo, "a.txt", "2", "change")

    rm.rollback_to(snap)
    assert (repo / "a.txt").read_text() == "1"


def test_rollback_after_failed_conversion(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    commit_file(repo, "a.txt", "1", "init")

    rm = RollbackManager(repo)
    snap = rm.create_snapshot("op")

    (repo / "a.txt").write_text("oops")
    rm.rollback_to(snap)
    assert (repo / "a.txt").read_text() == "1"


def test_rollback_with_uncommitted_changes(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    commit_file(repo, "a.txt", "1", "init")

    rm = RollbackManager(repo)
    snap = rm.create_snapshot("op")

    (repo / "b.txt").write_text("new")
    (repo / "a.txt").write_text("2")
    rm.rollback_to(snap)

    assert (repo / "a.txt").read_text() == "1"
    assert not (repo / "b.txt").exists()


def test_rollback_history_limit(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    commit_file(repo, "a.txt", "1", "init")

    rm = RollbackManager(repo, max_history=2)
    snap1 = rm.create_snapshot("one")
    snap2 = rm.create_snapshot("two")
    snap3 = rm.create_snapshot("three")

    snaps = [p.parent.name for p in sorted((repo / ".workflow-rollbacks").glob("*/metadata.json"))]
    assert len(snaps) == 2
    assert snap2 in snaps and snap3 in snaps


def test_corrupted_snapshot_handling(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    init_repo(repo)
    commit_file(repo, "a.txt", "1", "init")

    rm = RollbackManager(repo)
    snap = rm.create_snapshot("op")
    (repo / ".workflow-rollbacks" / snap / "metadata.json").write_text("{")

    assert not rm.verify_snapshot(snap)
    assert not rm.rollback_to(snap)
