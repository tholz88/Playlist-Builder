# tests/conftest.py
import os
import sys
import importlib
import types
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "dummy")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "dummy")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://localhost:5000/spotify/callback")
    monkeypatch.setenv("SPOTIFY_MARKET", "CH")
    yield

@pytest.fixture()
def app(monkeypatch):
    import main as main_module
    importlib.reload(main_module)
    main_module._spotify_token = None
    main_module._spotify_token_exp = 0
    main_module.playlist.clear()
    return main_module.app

@pytest.fixture()
def client(app):
    return app.test_client()

# ---- Fake Response helper ----
class FakeResp:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self):
        return self._json

@pytest.fixture()
def fake_requests(monkeypatch):
    ns = types.SimpleNamespace()

    def _default_get(*args, **kwargs):
        return FakeResp(200, {})

    def _default_post(*args, **kwargs):
        return FakeResp(200, {})

    ns.get = _default_get
    ns.post = _default_post

    import main as main_module
    monkeypatch.setattr(main_module.requests, "get", lambda *a, **k: ns.get(*a, **k))
    monkeypatch.setattr(main_module.requests, "post", lambda *a, **k: ns.post(*a, **k))

    return ns