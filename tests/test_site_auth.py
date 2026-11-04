"""Site config changes require the access key when ACCESS_KEY is set."""

import pytest

KEY = "secret"
NEW_SITE = {"name": "New", "baseUrl": "https://new.example"}

REQUESTS = [
    ("post", "/sites/new-site", NEW_SITE),
    ("delete", "/sites/modal", None),
    ("post", "/api/add-site", {"site_id": "new-site", **NEW_SITE}),
    ("delete", "/api/sites/modal", None),
    ("post", "/api/sites/reset", None),
]


@pytest.fixture
def locked(server, monkeypatch):
    monkeypatch.setattr(server, "ACCESS_KEY", KEY)
    return server


@pytest.mark.parametrize("method,path,body", REQUESTS)
def test_rejects_missing_key(client, locked, method, path, body):
    resp = client.request(method, path, json=body)
    assert resp.status_code == 401
    assert locked.sites_dict == {}


@pytest.mark.parametrize("method,path,body", REQUESTS)
def test_rejects_wrong_key(client, locked, method, path, body):
    resp = client.request(method, path, json=body, headers={"X-Access-Key": "nope"})
    assert resp.status_code == 401


@pytest.mark.parametrize("method,path,body", REQUESTS)
def test_accepts_valid_key(client, locked, method, path, body):
    resp = client.request(method, path, json=body, headers={"X-Access-Key": KEY})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_no_key_configured_allows_changes(client, server):
    resp = client.post("/sites/new-site", json=NEW_SITE)
    assert resp.status_code == 200
    assert "new-site" in server.sites_dict["_all_sites"]
