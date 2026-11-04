"""Offline tests for api/server.py endpoints."""


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}


def test_list_sites(client, server):
    data = client.get("/sites").json()
    assert data["count"] == len(server.load_sites_from_file())
    assert {"id": "modal"} in data["sites"]


def test_content_scrapes_then_caches(client, worker):
    first = client.get("/sites/modal/content", params={"path": "/guide"}).json()
    assert first["from_cache"] is False
    assert first["content"] == "content for modal/guide"

    second = client.get("/sites/modal/content", params={"path": "/guide"}).json()
    assert second["from_cache"] is True
    assert len(worker.scrape_content.calls) == 1


def test_unknown_site_404(client):
    assert client.get("/sites/nope/content").status_code == 404
