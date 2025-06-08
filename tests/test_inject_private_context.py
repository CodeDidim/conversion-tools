import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.inject_private_context import inject_context


def test_inject_context_with_overlay(tmp_path):
    src = tmp_path / "src"
    overlay = tmp_path / "overlay"
    dst = tmp_path / "dst"
    src.mkdir()
    overlay.mkdir()

    (src / "config.yaml").write_text("ip: {{ STM32_IP }}\n")
    (src / "notes.txt").write_text("token {{ STM32_IP }}\n")

    (overlay / "README.md").write_text("Overlay host {{ HOST }}\n")
    (overlay / "extra.py").write_text("ADDR='{{ STM32_IP }}'\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("STM32_IP: 10.0.0.1\nHOST: example.com\n")

    inject_context(src, dst, profile, overlay)

    assert (dst / "config.yaml").read_text() == "ip: 10.0.0.1\n"
    assert (dst / "notes.txt").read_text() == "token {{ STM32_IP }}\n"
    assert (dst / "README.md").read_text() == "Overlay host example.com\n"
    assert (dst / "extra.py").read_text() == "ADDR='10.0.0.1'\n"


def test_inject_context_without_overlay(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    (src / "file.md").write_text("use {{ VALUE }}\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("VALUE: data\n")

    inject_context(src, dst, profile)

    assert (dst / "file.md").read_text() == "use data\n"
