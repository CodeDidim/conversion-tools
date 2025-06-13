import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow


def test_manual_cycle(tmp_path):
    cfg = tmp_path / 'config.yaml'
    profile = tmp_path / 'profile.yaml'
    template = tmp_path / 'template'
    template.mkdir()
    (template / 'f.txt').write_text('z={{Z}}\n')
    profile.write_text('Z: 9\n')
    cfg.write_text(f'profile: "{profile}"\ntemp_dir: "{tmp_path}"\ntemplate: "{template}"\n')

    workflow.private_workflow(cfg)
    export_dir = workflow.public_workflow(cfg)
    assert (export_dir / 'f.txt').read_text() == 'z={{ Z }}\n'
