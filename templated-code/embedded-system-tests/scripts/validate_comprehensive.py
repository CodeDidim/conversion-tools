#!/usr/bin/env python3
"""Validate Integration Test Framework setup in the templated repository."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import List


class FrameworkValidator:
    """Validate directory structure and module imports for the framework."""

    def __init__(self) -> None:
        # Paths relative to repository root (executed from root)
        self.framework_path = Path.cwd() / "templated-code" / "integration-test-framework"
        self.tests_path = Path.cwd() / "templated-code" / "embedded-system-tests"
        self.errors: List[str] = []

    def _check_path(self, path: Path, desc: str) -> bool:
        if path.exists():
            print(f"  \u2713 {desc}: {path}")
            return True
        print(f"  \u2717 {desc}: {path} NOT FOUND")
        self.errors.append(f"Missing {desc} at {path}")
        return False

    def validate_structure(self) -> bool:
        print("\n\U0001F4C1 Checking directory structure...")
        ok = True
        ok &= self._check_path(
            self.framework_path / "src" / "integration_test_framework",
            "Framework src",
        )
        ok &= self._check_path(
            self.framework_path / "src" / "integration_test_framework" / "hal",
            "HAL module",
        )
        ok &= self._check_path(
            self.framework_path
            / "src"
            / "integration_test_framework"
            / "robot_framework"
            / "libraries",
            "Robot libraries",
        )
        ok &= self._check_path(self.tests_path / "config", "Test config")
        suites = self.tests_path / "tests" / "robot" / "suites"
        ok &= self._check_path(suites, "Test suites")
        if ok:
            robot_files = list(suites.rglob("*.robot"))
            if not robot_files:
                self.errors.append("No .robot files found in test suites")
                print("  \u2717 No .robot files found in test suites")
                ok = False
            else:
                print(f"  \u2713 Found {len(robot_files)} Robot Framework tests")
        return ok

    def validate_imports(self) -> bool:
        print("\n\U0001F4E6 Checking framework imports...")
        src_path = self.framework_path / "src"
        framework_src = str(src_path)
        if framework_src not in sys.path:
            sys.path.insert(0, framework_src)
        modules = [
            "integration_test_framework",
            "integration_test_framework.hal.interface",
            "integration_test_framework.hal.factory",
            "integration_test_framework.hal.channel_manager",
            "integration_test_framework.robot_framework.libraries.configurable_hal_library",
            "integration_test_framework.config.loader",
        ]
        success = True
        for mod in modules:
            try:
                importlib.import_module(mod)
                print(f"  \u2713 {mod}")
            except Exception as exc:  # noqa: BLE001
                print(f"  \u2717 {mod}: {exc}")
                self.errors.append(f"Failed to import {mod}: {exc}")
                success = False
        return success

    def run(self) -> None:
        structure_ok = self.validate_structure()
        import_ok = self.validate_imports()
        if structure_ok and import_ok:
            print("\nAll checks passed \u2714")
            return
        print("\nSome checks failed:")
        for err in self.errors:
            print(f"- {err}")
        print("\nEnsure the repository was generated correctly and dependencies are installed.")
        sys.exit(1)


if __name__ == "__main__":
    FrameworkValidator().run()
