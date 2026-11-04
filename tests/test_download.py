"""/sites/{site_id}/download skips assets and unsafe paths."""

import io
import time
import zipfile


def test_download_skips_assets_and_unsafe_paths(client, server, worker):
    base = "https://modal.com/docs"
    links = [
        f"{base}/guide",
        f"{base}/guide/nested",
        f"{base}/logo.png",
        f"{base}/manual.pdf",
        f"{base}/../../etc/passwd",
        "https://modal.com/a/../../../escape",
    ]
    server.cache["modal:links"] = {"links": links, "count": len(links), "timestamp": time.time()}

    resp = client.get("/sites/modal/download")
    assert resp.status_code == 200

    names = set(zipfile.ZipFile(io.BytesIO(resp.content)).namelist())
    assert names == {"modal/guide.md", "modal/guide/nested.md", "modal/README.md"}
    assert all(".." not in n and not n.startswith("/") for n in names)
    scraped = {args[1] for args in worker.scrape_content.calls}
    assert scraped == {"/guide", "/guide/nested"}
