import pytest
from pathlib import Path

@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project structure for testing"""
    project = tmp_path / "test_project"
    project.mkdir()
    (project / "README.md").write_text("sample project")
    return project


@pytest.fixture
def company_profile():
    """Standard company profile for testing"""
    return {
        "COMPANY_NAME": "ACME Corp",
        "API_KEY": "sk-test-12345",
        "DB_PASSWORD": "super$ecret",
    }


@pytest.fixture
def workflow_config():
    """Standard workflow configuration"""
    return {
        "github": {"owner": "testuser", "repo": "test-repo"},
    }
