import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.apply_template_context import inject_context
from scripts.revert_template_context import revert_context
from core.utils import sanitize_identifier, is_valid_identifier


class TestIdentifierEdgeCases:
    """Test placeholder handling in Python identifiers."""
    
    def test_sanitize_identifier(self):
        """Test identifier sanitization."""
        assert sanitize_identifier("ACME Corp") == "ACME_Corp"
        assert sanitize_identifier("123-start") == "start"
        assert sanitize_identifier("my-variable-name") == "my_variable_name"
        assert sanitize_identifier("class") == "var_class"
        assert sanitize_identifier("") == "unnamed"
        assert sanitize_identifier("___") == "unnamed"
        
    def test_class_name_with_spaces(self, tmp_path):
        """Test class name placeholder with spaces in value."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "client.py").write_text(
            "class {{ COMPANY_NAME }}Client:\n"
            "    def __init__(self):\n"
            "        self.name = '{{ COMPANY_NAME }}'\n"
        )
        
        profile = tmp_path / "profile.yaml"
        profile.write_text("COMPANY_NAME: 'ACME Corp'\n")
        
        dst = tmp_path / "dst"
        inject_context(src, dst, profile)
        
        result = (dst / "client.py").read_text()
        # Should have sanitized class name but regular string value
        assert "class ACME_CorpClient:" in result
        assert "self.name = 'ACME Corp'" in result
        
    def test_function_name_with_special_chars(self, tmp_path):
        """Test function name with special characters."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "utils.py").write_text(
            "def get_{{ METRIC_TYPE }}_data():\n"
            "    return '{{ METRIC_TYPE }}'\n"
        )
        
        profile = tmp_path / "profile.yaml"
        profile.write_text("METRIC_TYPE: 'real-time'\n")
        
        dst = tmp_path / "dst"
        inject_context(src, dst, profile)
        
        result = (dst / "utils.py").read_text()
        assert "def get_real_time_data():" in result
        assert "return 'real-time'" in result
        
    def test_revert_sanitized_identifiers(self, tmp_path):
        """Test reverting sanitized identifiers back to placeholders."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text(
            "class ACME_CorpClient:\n"
            "    company = 'ACME Corp'\n"
        )
        
        profile = tmp_path / "profile.yaml"
        profile.write_text("COMPANY_NAME: 'ACME Corp'\n")
        
        dst = tmp_path / "dst"
        revert_context(src, dst, profile)
        
        result = (dst / "app.py").read_text()
        assert "class {{ COMPANY_NAME }}Client:" in result
        assert "company = '{{ COMPANY_NAME }}'" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

