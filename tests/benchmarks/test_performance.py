import sys
import time
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - Windows
    resource = None
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.apply_template_context import inject_context


def test_large_repository_conversion_time(tmp_path):
    """Ensure conversion completes in reasonable time"""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    profile = tmp_path / "p.yaml"
    profile.write_text("K: v")
    for i in range(200):
        (src / f"f{i}.txt").write_text("{{K}}\n" * 10)
    start = time.perf_counter()
    inject_context(src, dst, profile)
    duration = time.perf_counter() - start
    assert duration < 5


@pytest.mark.skipif(resource is None, reason="resource module not available")
def test_memory_usage_during_conversion(tmp_path):
    """Ensure memory usage stays reasonable"""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    profile = tmp_path / "p.yaml"
    profile.write_text("K: v")
    for i in range(100):
        (src / f"f{i}.txt").write_text("{{K}}\n")
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    inject_context(src, dst, profile)
    end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert end_mem - start_mem < 200_000_000
