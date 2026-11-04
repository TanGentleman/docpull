"""The /api/* routes used by the UI must behave like their raw counterparts."""

import time


def test_api_content_cache_hit(client, server):
    server.cache["modal:/guide"] = {"content": "cached", "url": "u", "timestamp": time.time()}
    resp = client.get("/api/sites/modal/content", params={"path": "/guide"})
    assert resp.status_code == 200
    assert resp.json()["from_cache"] is True


def test_api_content_post_cache_hit(client, server):
    server.cache["modal:/guide"] = {"content": "cached", "url": "u", "timestamp": time.time()}
    resp = client.post("/api/content", json={"site_id": "modal", "path": "/guide"})
    assert resp.status_code == 200
    assert "cached" in resp.json()["stdout"]


def test_api_links_cache_hit(client, server):
    links = ["https://modal.com/docs/a", "https://modal.com/docs/b"]
    server.cache["modal:links"] = {"links": links, "count": 2, "timestamp": time.time()}
    resp = client.get("/api/sites/modal/links")
    assert resp.status_code == 200
    assert resp.json()["links"] == links


def test_api_jobs(client, server):
    server.jobs["abc"] = {
        "status": "completed", "created_at": time.time(),
        "input": {"sites": ["modal"], "to_scrape": 1}, "progress": {"completed": 1},
    }
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert resp.json()["jobs"][0]["job_id"] == "abc"


def test_api_sites_omits_test_paths(client):
    sites = client.get("/api/sites").json()["sites"]
    assert all(set(s) == {"id"} for s in sites)
