from pathlib import Path

class MockGitHub:
    """Mock GitHub API for testing without real API calls"""
    def __init__(self):
        self.visibility = "private"
        self.api_calls = []

    def set_visibility(self, private: bool):
        """Simulate visibility change"""
        self.visibility = "private" if private else "public"
        self.api_calls.append(f"set_visibility:{self.visibility}")

    def get_visibility(self) -> str:
        """Return current visibility"""
        return self.visibility


class MockGitRepository:
    """Mock git operations for predictable testing"""
    def __init__(self, working_directory: Path):
        self.repo_dir = working_directory
        self.commits = []
        self.branches = {"main": None}
        self.current_branch = "main"


class MockFileSystem:
    """Mock filesystem operations for testing edge cases"""
    def __init__(self):
        self.space_available = float('inf')
        self.permission_errors = set()
