from __future__ import annotations
import json
import shutil
import subprocess
# Use timezone-aware timestamps to avoid ambiguity in comparisons and logging
# Rollbacks use UTC so snapshots are consistent across environments
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, List, Optional


class RollbackManager:
    """Manage workflow rollback snapshots."""

    def __init__(self, root_dir: Path, max_history: int = 5) -> None:
        self.root_dir = root_dir
        self.max_history = max_history
        self.storage = self.root_dir / ".workflow-rollbacks"
        self.storage.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    def _run_git(self, *args: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _hash_tracked_files(self) -> str:
        files_list = self._run_git("ls-files")
        if not files_list:
            return ""
        hasher = sha256()
        for rel in files_list.splitlines():
            path = self.root_dir / rel
            if path.is_file():
                hasher.update(rel.encode())
                hasher.update(path.read_bytes())
        return hasher.hexdigest()

    def _copy_tracked_files(self, dst: Path) -> None:
        """Copy tracked files with robust error handling."""
        files_list = self._run_git("ls-files")
        if not files_list:
            return

        dst = Path(dst)
        successful_copies = 0
        failed_copies = 0

        for rel in files_list.splitlines():
            try:
                src = self.root_dir / rel

                # Skip if source doesn't exist
                if not src.exists():
                    print(f"Info: Tracked file not in working tree: {rel}")
                    continue

                # Skip directories
                if src.is_dir():
                    print(f"Info: Skipping directory: {rel}")
                    continue

                if src.is_file():
                    target = dst / rel

                    # Create parent directories
                    target.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(src, target)
                    successful_copies += 1

            except Exception as e:
                failed_copies += 1
                print(f"Warning: Could not copy {rel}: {e}")
                continue

        print(f"Rollback snapshot: {successful_copies} files copied, {failed_copies} failed")
            
            
# ------------------------------------------------------------------
    def create_snapshot(self, operation: str, config_snapshot: Optional[Dict] = None) -> str:
        # Use UTC so snapshot timestamps sort consistently regardless of local timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        snap_dir = self.storage / ts
        snap_dir.mkdir(parents=True, exist_ok=True)
        files_dir = snap_dir / "files"
        files_dir.mkdir()

        branch = self._run_git("rev-parse", "--abbrev-ref", "HEAD") or ""
        commit = self._run_git("rev-parse", "HEAD") or ""
        status = self._run_git("status", "--porcelain") or ""
        dirty = [line[3:] for line in status.splitlines() if line and line[0] != " "]

        self._copy_tracked_files(files_dir)

        meta = {
            "timestamp": ts,
            "operation": operation,
            "branch": branch,
            "commit": commit,
            "files_hash": self._hash_tracked_files(),
            "config_snapshot": config_snapshot or {},
            "dirty_files": dirty,
        }
        (snap_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
        (snap_dir / "git-state.json").write_text(
            json.dumps({"branch": branch, "commit": commit, "status": status}, indent=2)
        )

        self.cleanup_old_snapshots()
        return ts

    def list_snapshots(self) -> List[Dict]:
        snaps: List[Dict] = []
        for path in sorted(self.storage.glob("*/metadata.json")):
            try:
                data = json.loads(path.read_text())
                snaps.append(data)
            except Exception:
                continue
        snaps.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return snaps

    def verify_snapshot(self, snapshot_id: str) -> bool:
        snap = self.storage / snapshot_id
        meta_file = snap / "metadata.json"
        files_dir = snap / "files"
        if not meta_file.exists() or not files_dir.is_dir():
            return False
        try:
            json.loads(meta_file.read_text())
        except Exception:
            return False
        return True

    def rollback_to(self, snapshot_id: str, dry_run: bool = False) -> bool:
        if not self.verify_snapshot(snapshot_id):
            return False
        snap = self.storage / snapshot_id
        meta = json.loads((snap / "metadata.json").read_text())
        if dry_run:
            return True

        branch = meta.get("branch")
        commit = meta.get("commit")
        if branch and commit:
            self._run_git("checkout", branch)
            self._run_git("reset", "--hard", commit)
            self._run_git("clean", "-fd")

        files_dir = snap / "files"
        for src in files_dir.rglob("*"):
            if src.is_file():
                rel = src.relative_to(files_dir)
                dst = self.root_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        return True

    def cleanup_old_snapshots(self) -> None:
        snaps = sorted(self.storage.glob("*/metadata.json"))
        if len(snaps) <= self.max_history:
            return
        to_remove = snaps[:-self.max_history]
        for meta in to_remove:
            shutil.rmtree(meta.parent, ignore_errors=True)

