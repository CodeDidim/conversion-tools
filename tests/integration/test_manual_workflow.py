import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import workflow
import shutil


class TestManualWorkflowEndToEnd:
    """Test complete manual workflow scenarios"""

    def test_home_to_company_flow(self):
        cfg = Path("config.yaml")
        profile = Path("profile.yaml")
        template = Path("template")
        template.mkdir()
        (template / "app.txt").write_text("v={{V}}")
        profile.write_text("V: 1\n")
        cfg.write_text(
            f"profile: \"{profile}\"\ntemp_dir: \"work\"\ntemplate: \"{template}\"\n"
        )
        private_dir = workflow.private_workflow(cfg)
        assert (private_dir / "app.txt").read_text() == "v=1"

    def test_company_to_home_flow(self):
        cfg = Path("config.yaml")
        profile = Path("profile.yaml")
        template = Path("template")
        template.mkdir()
        (template / "app.txt").write_text("v={{V}}")
        profile.write_text("V: 2\n")
        cfg.write_text(
            f"profile: \"{profile}\"\ntemp_dir: \"work\"\ntemplate: \"{template}\"\n"
        )
        private_dir = workflow.private_workflow(cfg)
        public_dir = workflow.public_workflow(cfg)
        assert (public_dir / "app.txt").read_text() == "v={{ V }}"

    def test_multi_developer_collaboration(self):
        cfg = Path("config.yaml")
        profile = Path("profile.yaml")
        template = Path("template")
        template.mkdir()
        (template / "a.txt").write_text("v={{V}}")
        profile.write_text("V: 1\n")
        cfg.write_text(
            f"profile: \"{profile}\"\ntemp_dir: \"work\"\ntemplate: \"{template}\"\n"
        )
        workflow.private_workflow(cfg)
        (Path("work/private") / "a.txt").write_text("changed1")
        workflow.public_workflow(cfg)

        profile.write_text("V: 2\n")
        shutil.rmtree("work", ignore_errors=True)
        workflow.private_workflow(cfg)
        (Path("work/private") / "a.txt").write_text("changed2")
        workflow.public_workflow(cfg)
        assert (Path("work/export") / "a.txt").exists()


def test_manual_cycle(tmp_path):
    cfg = tmp_path / "config.yaml"
    profile = tmp_path / "profile.yaml"
    template = tmp_path / "template"
    template.mkdir()
    (template / "f.txt").write_text("z={{Z}}\n")
    profile.write_text("Z: 9\n")
    cfg.write_text(f"profile: \"{profile}\"\ntemp_dir: \"{tmp_path}\"\ntemplate: \"{template}\"\n")

    workflow.private_workflow(cfg)
    export_dir = workflow.public_workflow(cfg)
    assert (export_dir / "f.txt").read_text() == "z={{ Z }}\n"
