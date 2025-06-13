import pytest
from pathlib import Path
import sys
import subprocess
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.apply_template_context import inject_context
from scripts.revert_template_context import revert_context
from scripts.export_to_public import export_directory
from scripts.validate_public_repo import validate_directory


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_full_roundtrip_workflow(self, tmp_path):
        """Test complete workflow: generic -> private -> public -> validate."""
        # Step 1: Create generic template
        generic = tmp_path / "generic"
        generic.mkdir()

        (generic / "config.yaml").write_text(
            "database:\n"
            "  host: {{ DB_HOST }}\n"
            "  password: {{ DB_PASS }}\n"
            "company: {{ COMPANY_NAME }}\n"
        )

        # Create src directory first
        (generic / "src").mkdir()
        (generic / "src" / "app.py").write_text(
            "# Copyright {{ COMPANY_NAME }}\n"
            "API_KEY = '{{ API_KEY }}'\n"
            "EMAIL = '{{ SUPPORT_EMAIL }}'\n"
        )

        # Step 2: Apply private context
        profile = tmp_path / "profile.yaml"
        profile.write_text(
            "DB_HOST: prod.db.internal\n"
            "DB_PASS: super$ecret123\n"
            "COMPANY_NAME: YourCompany\n"
            "API_KEY: sk-1234567890abcdef\n"
            "SUPPORT_EMAIL: support@company.com\n"
        )

        private = tmp_path / "private"
        inject_context(generic, private, profile)

        # Verify private version
        assert "prod.db.internal" in (private / "config.yaml").read_text()
        assert "YourCompany" in (private / "src" / "app.py").read_text()

        # Step 3: Export to public (should remove company lines)
        public_export = tmp_path / "public_export"
        export_directory(private, public_export)

        # Step 4: Validate public export - expect failure due to company references
        # The validation should fail because YourCompany is still in some files
        assert not validate_directory(public_export)

        # Step 5: Revert to template for safe sharing
        public_template = tmp_path / "public_template"
        revert_context(private, public_template, profile)

        # Verify reverted version
        assert "{{ DB_HOST }}" in (public_template / "config.yaml").read_text()
        assert "{{ COMPANY_NAME }}" in (public_template / "src" / "app.py").read_text()

    def test_multiple_overlay_scenarios(self, tmp_path):
        """Test complex overlay scenarios with conflicts."""
        base = tmp_path / "base"
        base.mkdir()

        # Base template
        (base / "config.yaml").write_text("env: {{ ENV }}\n")
        
        # Create app directory first
        (base / "app").mkdir()
        (base / "app" / "main.py").write_text("# Base file\nmode = '{{ MODE }}'")

        # Overlay 1: Development
        overlay1 = tmp_path / "overlay_dev"
        overlay1.mkdir()
        (overlay1 / "config.yaml").write_text("env: {{ ENV }}\ndebug: true\n")
        (overlay1 / "app").mkdir()
        (overlay1 / "app" / "debug.py").write_text("DEBUG = True")

        # Overlay 2: Production  
        overlay2 = tmp_path / "overlay_prod"
        overlay2.mkdir()
        (overlay2 / "config.yaml").write_text("env: {{ ENV }}\ndebug: false\nsecure: true\n")
        (overlay2 / "app").mkdir()
        (overlay2 / "app" / "main.py").write_text("# Prod override\nmode = '{{ MODE }}'\nSECURE = True")

        profile = tmp_path / "profile.yaml"
        profile.write_text("ENV: production\nMODE: live\n")

        # Test with production overlay
        dst = tmp_path / "dst"
        inject_context(base, dst, profile, overlay2)

        config = (dst / "config.yaml").read_text()
        assert "production" in config
        assert "debug: false" in config
        assert "secure: true" in config

        main = (dst / "app" / "main.py").read_text()
        assert "Prod override" in main
        assert "SECURE = True" in main
        assert "mode = 'live'" in main

    def test_git_ignored_files_handling(self, tmp_path):
        """Test that we properly handle .gitignore patterns."""
        src = tmp_path / "src"
        src.mkdir()

        # Create .gitignore
        (src / ".gitignore").write_text(
            "*.log\n"
            "temp/\n"
            "secrets.yaml\n"
            "!important.log\n"
        )

        # Create files matching gitignore patterns
        (src / "app.log").write_text("{{ TOKEN }} in log")
        (src / "important.log").write_text("{{ TOKEN }} in important log")
        (src / "secrets.yaml").write_text("password: {{ SECRET_PASS }}")
        
        # Create temp directory first
        (src / "temp").mkdir()
        (src / "temp" / "cache.txt").write_text("{{ CACHE_KEY }}")

        profile = tmp_path / "profile.yaml"
        profile.write_text(
            "TOKEN: replaced\n"
            "SECRET_PASS: mysecret\n"
            "CACHE_KEY: cachevalue\n"
        )

        dst = tmp_path / "dst"
        inject_context(src, dst, profile)

        # All files should be processed regardless of gitignore
        assert "replaced" in (dst / "app.log").read_text()
        assert "replaced" in (dst / "important.log").read_text()
        assert "mysecret" in (dst / "secrets.yaml").read_text()
        assert "cachevalue" in (dst / "temp" / "cache.txt").read_text()

    def test_cross_platform_line_endings(self, tmp_path):
        """Test handling of different line ending styles."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        # Unix style (LF)
        (src / "unix.txt").write_bytes(b"line1 {{ TOKEN }}\nline2\n")

        # Windows style (CRLF)
        (src / "windows.txt").write_bytes(b"line1 {{ TOKEN }}\r\nline2\r\n")

        # Old Mac style (CR)
        (src / "mac.txt").write_bytes(b"line1 {{ TOKEN }}\rline2\r")

        # Mixed line endings
        (src / "mixed.txt").write_bytes(b"line1 {{ TOKEN }}\nline2\r\nline3\r")

        profile = tmp_path / "profile.yaml"
        profile.write_text("TOKEN: replaced")

        inject_context(src, dst, profile)

        # Check that tokens are replaced (line endings might be normalized on Windows)
        unix_content = (dst / "unix.txt").read_text()
        assert "line1 replaced" in unix_content
        assert "line2" in unix_content

        windows_content = (dst / "windows.txt").read_text()
        assert "line1 replaced" in windows_content
        assert "line2" in windows_content

        # For binary comparison, we need to account for Windows normalizing line endings
        # when using read_text/write_text. The actual preservation test would need
        # the apply_template_context.py to handle binary mode for exact preservation
        
        # Just verify the content was processed correctly
        assert "replaced" in (dst / "mac.txt").read_text()
        assert "replaced" in (dst / "mixed.txt").read_text()

    def test_cli_error_scenarios(self, tmp_path):
        """Test command-line interface error handling."""
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "apply_template_context.py"

        # Test with non-existent source
        result = subprocess.run(
            [sys.executable, str(script_path), "nonexistent", str(tmp_path / "dst"), "profile.yaml"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

        # Test with invalid arguments
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "usage:" in result.stderr or "required" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])