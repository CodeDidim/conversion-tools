import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import workflow
import shutil


class TestManualWorkflowEndToEnd:
    """Test complete manual workflow scenarios"""

    def test_home_to_company_flow(self, tmp_path):
        cfg = tmp_path / "config.yaml"
        placeholder_values = tmp_path / "profile.yaml"
        template_source_dir = tmp_path / "template"
        template_source_dir.mkdir()
        (template_source_dir / "app.txt").write_text("v={{V}}")
        placeholder_values.write_text("V: 1\n")
        cfg.write_text(
            f"placeholder_values: \"{placeholder_values.as_posix()}\"\n"
            f"working_directory: \"{tmp_path.as_posix()}\"\n"
            f"template_source_dir: \"{template_source_dir.as_posix()}\"\n"
        )
        private_dir = workflow.private_workflow(cfg)
        assert (private_dir / "app.txt").read_text() == "v=1"

    def test_company_to_home_flow(self, tmp_path):
        cfg = tmp_path / "config.yaml"
        placeholder_values = tmp_path / "profile.yaml"
        template_source_dir = tmp_path / "template"
        template_source_dir.mkdir()
        (template_source_dir / "app.txt").write_text("v={{V}}")
        placeholder_values.write_text("V: 2\n")
        cfg.write_text(
            f"placeholder_values: \"{placeholder_values.as_posix()}\"\n"
            f"working_directory: \"{tmp_path.as_posix()}\"\n"
            f"template_source_dir: \"{template_source_dir.as_posix()}\"\n"
        )
        private_dir = workflow.private_workflow(cfg)
        public_dir = workflow.public_workflow(cfg)
        assert (public_dir / "app.txt").read_text() == "v={{V}}"

    def test_multi_developer_collaboration(self, tmp_path):
        cfg = tmp_path / "config.yaml"
        placeholder_values = tmp_path / "profile.yaml"
        template_source_dir = tmp_path / "template"
        template_source_dir.mkdir()
        (template_source_dir / "a.txt").write_text("v={{V}}")
        placeholder_values.write_text("V: 1\n")
        cfg.write_text(
            f"placeholder_values: \"{placeholder_values.as_posix()}\"\n"
            f"working_directory: \"{tmp_path.as_posix()}\"\n"
            f"template_source_dir: \"{template_source_dir.as_posix()}\"\n"
        )
        workflow.private_workflow(cfg)
        (tmp_path / "private" / "a.txt").write_text("changed1")
        workflow.public_workflow(cfg)

        placeholder_values.write_text("V: 2\n")
        shutil.rmtree(tmp_path / "private", ignore_errors=True)
        shutil.rmtree(tmp_path / "public", ignore_errors=True)
        workflow.private_workflow(cfg)
        (tmp_path / "private" / "a.txt").write_text("changed2")
        workflow.public_workflow(cfg)
        assert (tmp_path / "public" / "a.txt").exists()


def test_manual_cycle(tmp_path):
    cfg = tmp_path / "config.yaml"
    placeholder_values = tmp_path / "profile.yaml"
    template_source_dir = tmp_path / "template"
    template_source_dir.mkdir()
    (template_source_dir / "f.txt").write_text("z={{Z}}\n")
    placeholder_values.write_text("Z: 9\n")
    cfg.write_text(
        f"placeholder_values: \"{placeholder_values.as_posix()}\"\n"
        f"working_directory: \"{tmp_path.as_posix()}\"\n"
        f"template_source_dir: \"{template_source_dir.as_posix()}\"\n"
    )

    workflow.private_workflow(cfg)
    public_dir = workflow.public_workflow(cfg)
    assert (public_dir / "f.txt").read_text() == "z={{Z}}\n"
