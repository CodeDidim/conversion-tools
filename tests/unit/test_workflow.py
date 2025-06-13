import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow


def test_private_public_cycle(tmp_path):
    cfg = tmp_path / 'config.yaml'
    profile = tmp_path / 'profile.yaml'
    template = tmp_path / 'template'
    overlay = tmp_path / 'overlay'
    work = tmp_path / 'work'
    template.mkdir()
    overlay.mkdir()
    (template / 'a.txt').write_text('x={{X}}\n')
    (overlay / 'b.txt').write_text('y={{Y}}\n')
    profile.write_text('X: 1\nY: 2\n')
    cfg.write_text(f'profile: "{profile}"\noverlay_dir: "{overlay}"\ntemp_dir: "{work}"\ntemplate: "{template}"\n')

    private_dir = workflow.private_workflow(cfg)
    assert (private_dir / 'a.txt').read_text() == 'x=1\n'
    assert (private_dir / 'b.txt').read_text() == 'y=2\n'

    export_dir = workflow.public_workflow(cfg)
    assert (export_dir / 'a.txt').exists()

