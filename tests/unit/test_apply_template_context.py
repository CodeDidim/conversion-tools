import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.apply_template_context import inject_context


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
    assert (dst / "notes.txt").read_text() == "token 10.0.0.1\n"
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


def test_inject_context_token_no_spaces(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    (src / "file.txt").write_text("var={{VALUE}}\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("VALUE: 42\n")

    inject_context(src, dst, profile)

    assert (dst / "file.txt").read_text() == "var=42\n"


def test_overlay_symlink_within(tmp_path):
    src = tmp_path / "src"
    overlay = tmp_path / "overlay"
    dst = tmp_path / "dst"
    src.mkdir()
    overlay.mkdir()

    (src / "base.txt").write_text("base")
    (overlay / "real.txt").write_text("Val {{ KEY }}")
    (overlay / "link.txt").symlink_to("real.txt")

    profile = tmp_path / "profile.yaml"
    profile.write_text("KEY: X\n")

    inject_context(src, dst, profile, overlay)

    assert (dst / "link.txt").is_symlink()
    assert (dst / "real.txt").read_text() == "Val X"
    assert (dst / "link.txt").resolve() == (dst / "real.txt").resolve()


def test_overlay_symlink_outside(tmp_path):
    src = tmp_path / "src"
    overlay = tmp_path / "overlay"
    dst = tmp_path / "dst"
    src.mkdir()
    overlay.mkdir()

    (src / "base.txt").write_text("base")
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")
    (overlay / "link.txt").symlink_to(outside)

    profile = tmp_path / "profile.yaml"
    profile.write_text("")

    inject_context(src, dst, profile, overlay)

    assert not (dst / "link.txt").exists()


def test_overlay_broken_symlink(tmp_path):
    src = tmp_path / "src"
    overlay = tmp_path / "overlay"
    dst = tmp_path / "dst"
    src.mkdir()
    overlay.mkdir()

    (src / "base.txt").write_text("base")
    (overlay / "broken.data").symlink_to("missing.data")

    profile = tmp_path / "profile.yaml"
    profile.write_text("")

    inject_context(src, dst, profile, overlay)

    assert (dst / "broken.data").is_symlink()
