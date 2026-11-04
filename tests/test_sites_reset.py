"""POST /sites/reset isn't shadowed by POST /sites/{site_id}."""


def test_reset_restores_sites_from_file(client, server):
    server.sites_dict["_all_sites"] = {"only": {"name": "Only", "baseUrl": "https://only.example"}}

    resp = client.post("/sites/reset")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "modal" in body["sites"]
    assert "only" not in server.sites_dict["_all_sites"]


def test_add_site_still_works(client, server):
    resp = client.post("/sites/new", json={"name": "New", "baseUrl": "https://new.example"})
    assert resp.status_code == 200
    assert "new" in server.sites_dict["_all_sites"]
