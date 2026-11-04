"""Shared fixtures for offline tests of api/server.py.

Modal Dicts are swapped for plain dicts and PlaywrightWorker for a fake, so
tests run without Modal credentials or a browser.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SITES_JSON = Path(__file__).parent.parent / "config" / "sites.json"


class _Method:
    """Mimics a Modal method: `.remote.aio(...)`, `.remote(...)` and `.spawn(...)`."""

    def __init__(self, fn):
        self._fn = fn
        self.calls: list[tuple] = []
        self.remote = self
        self.spawned: list[tuple] = []

    def __call__(self, *args, **kwargs):
        self.calls.append(args)
        return self._fn(*args, **kwargs)

    async def aio(self, *args, **kwargs):
        return self(*args, **kwargs)

    def spawn(self, *args, **kwargs):
        self.spawned.append(args)


class FakeWorker:
    """Stand-in for PlaywrightWorker. Set `content_result` etc. to control output."""

    def __init__(self):
        self.content_result = lambda site_id, path, config: {
            "content": f"content for {site_id}{path}",
            "metadata": {"url": config["baseUrl"] + path},
        }
        self.links_result = lambda site_id, config: {"content": [], "metadata": {}}
        self.discover_result = lambda url: {"error": "not configured"}
        self.scrape_content = _Method(lambda *a: self.content_result(*a))
        self.scrape_links = _Method(lambda *a: self.links_result(*a))
        self.discover_selectors = _Method(lambda *a: self.discover_result(*a))
        self.process_batch = _Method(lambda *a: None)

    def __call__(self):
        return self


@pytest.fixture
def server(monkeypatch):
    """The api.server module with in-memory state and a fake worker."""
    import api.bulk as bulk
    import api.server as server

    sites = json.loads(SITES_JSON.read_text())["sites"]
    state = {"cache": {}, "error_tracker": {}, "sites_dict": {}, "jobs": {}}
    monkeypatch.setattr(server, "cache", state["cache"])
    monkeypatch.setattr(server, "error_tracker", state["error_tracker"])
    monkeypatch.setattr(server, "sites_dict", state["sites_dict"])
    monkeypatch.setattr(server, "jobs", state["jobs"])
    monkeypatch.setattr(bulk, "jobs", state["jobs"])
    monkeypatch.setattr(server, "load_sites_from_file", lambda: json.loads(json.dumps(sites)))
    monkeypatch.setattr(server, "PlaywrightWorker", FakeWorker())
    monkeypatch.setattr(server, "ACCESS_KEY", None)
    return server


@pytest.fixture
def worker(server) -> FakeWorker:
    return server.PlaywrightWorker


@pytest.fixture
def client(server) -> TestClient:
    return TestClient(server.web_app)
