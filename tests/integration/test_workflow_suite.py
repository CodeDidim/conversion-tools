import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow


def test_complete_workflow(tmp_path):
    template = tmp_path / "template"
    template.mkdir()
    (template / "a.txt").write_text("A={{A}}\n")
    (template / "b.txt").write_text("B={{B}}\n")

    overlay = tmp_path / "overlay"
    overlay.mkdir()
    (overlay / "secret.txt").write_text("S={{S}}\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("A: 1\nB: 2\nS: 3\n")

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"profile: '{profile}'\ntemp_dir: '{tmp_path}'\ntemplate: '{template}'\noverlay_dir: '{overlay}'\n"
    )

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / "a.txt").read_text() == "A=1\n"
    assert (private_dir / "b.txt").read_text() == "B=2\n"
    assert (private_dir / "secret.txt").read_text() == "S=3\n"

    public_dir = workflow.public_workflow(cfg)
    assert (public_dir / "a.txt").read_text() == "A={{A}}\n"
    assert (public_dir / "b.txt").read_text() == "B={{B}}\n"
    assert not (public_dir / "secret.txt").exists()


def test_edge_case_class_names(tmp_path):
    template = tmp_path / "template"
    template.mkdir()
    (template / "client.py").write_text("class {{ COMPANY_NAME }}Client:\n    pass\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("COMPANY_NAME: ACME\n")

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"profile: '{profile}'\ntemp_dir: '{tmp_path}'\ntemplate: '{template}'\n"
    )

    private_dir = workflow.private_workflow(cfg)
    assert "class ACMECli" in (private_dir / "client.py").read_text()

    public_dir = workflow.public_workflow(cfg)
    assert "{{ COMPANY_NAME }}Client" in (public_dir / "client.py").read_text()


def test_binary_file_protection(tmp_path):
    template = tmp_path / "template"
    template.mkdir()
    data = b"\x00\x01\x02\x03"
    (template / "file.bin").write_bytes(data)

    profile = tmp_path / "profile.yaml"
    profile.write_text("TOKEN: secret\n")

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        f"profile: '{profile}'\ntemp_dir: '{tmp_path}'\ntemplate: '{template}'\n"
    )

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / "file.bin").read_bytes() == data

    public_dir = workflow.public_workflow(cfg)
    assert (public_dir / "file.bin").read_bytes() == data
