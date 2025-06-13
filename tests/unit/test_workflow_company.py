import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import workflow_company


def test_company_private(tmp_path):
    cfg = tmp_path / 'config.yaml'
    profile = tmp_path / 'profile.yaml'
    template = tmp_path / 'template'
    template.mkdir()
    profile.write_text('K: v\n')
    cfg.write_text(f'profile: "{profile}"\ntemp_dir: "{tmp_path}"\ntemplate: "{template}"\n')

    private_dir = workflow_company.private_workflow(cfg)
    assert (private_dir / 'a.txt').exists() is False
