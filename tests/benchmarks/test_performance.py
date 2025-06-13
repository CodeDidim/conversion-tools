import sys
import time
from pathlib import Path
import resource

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.apply_template_context import inject_context


def test_large_repository_conversion_time():
    """Ensure conversion completes in reasonable time"""
    src = Path("src")
    dst = Path("dst")
    src.mkdir()
    profile = Path("p.yaml")
    profile.write_text("K: v")
    for i in range(200):
        (src / f"f{i}.txt").write_text("{{K}}\n" * 10)
    start = time.perf_counter()
    inject_context(src, dst, profile)
    duration = time.perf_counter() - start
    assert duration < 5


def test_memory_usage_during_conversion():
    """Ensure memory usage stays reasonable"""
    src = Path("src")
    dst = Path("dst")
    src.mkdir()
    profile = Path("p.yaml")
    profile.write_text("K: v")
    for i in range(100):
        (src / f"f{i}.txt").write_text("{{K}}\n")
    start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    inject_context(src, dst, profile)
    end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert end_mem - start_mem < 200_000_000
