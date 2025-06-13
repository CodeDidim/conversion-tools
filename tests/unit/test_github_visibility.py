from scripts.github_visibility import set_visibility
from urllib import request


def test_set_visibility(monkeypatch):
    recorded = {}

    def fake_open(req):
        recorded['url'] = req.full_url
        recorded['data'] = req.data
        recorded['auth'] = req.headers.get('Authorization')
        class Resp:
            status = 200
        return Resp()

    monkeypatch.setattr(request, 'urlopen', fake_open)
    set_visibility('owner', 'repo', True, 'tok')

    import json
    assert recorded['url'].endswith('/owner/repo')
    assert json.loads(recorded['data'].decode()) == {'private': True}
    assert recorded['auth'] == 'token tok'


