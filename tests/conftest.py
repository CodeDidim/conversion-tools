import pytest
from pathlib import Path


def pytest_configure(config):
    """Configure test markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


@pytest.fixture(autouse=True)
def test_isolation(tmp_path, monkeypatch):
    """Ensure tests don't affect real filesystem"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
