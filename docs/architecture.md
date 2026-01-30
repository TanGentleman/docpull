# Architecture

Bulk scraping with optimal batching across containers.

## Overview

```
POST /jobs/bulk (1000 URLs)
  → Filter assets (.pdf, .zip) → cache as links
  → Group by site_id
  → Calculate batches (URLs ÷ containers per site)
  → .spawn() workers (fire-and-forget)
  → Return job_id

SiteWorker containers (up to 100)
  → 1 browser per container
  → 1 site per container
  → Sequential scraping, 1s delay between requests
  → Write to cache, update job progress

GET /jobs/{job_id}
  → Check status anytime
```

## Example

1000 URLs: 200 each across 5 sites, 100 containers available.

| Step | Result |
|------|--------|
| Filter | 50 assets cached, 950 to scrape |
| Group | 5 sites × 190 URLs |
| Batch | 100 containers ÷ 5 sites = 20/site, ~10 URLs/container |
| Spawn | 100 workers |
| Time | 10 URLs × 2s ≈ 20 seconds total |

## Implementation

### Constants

```python
MAX_CONTAINERS = 100

ASSET_EXTENSIONS = {
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp4", ".mp3", ".wav", ".webm", ".mov",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".dmg", ".pkg", ".deb", ".rpm",
}

USER_AGENT = "DocPull/1.0 (+https://github.com/yourrepo/docpull) documentation archiver"
DEFAULT_DELAY_MS = 1000

jobs = modal.Dict.from_name("scrape-jobs", create_if_missing=True)
```

### Asset Detection & Grouping

```python
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath


def is_asset_url(url: str) -> bool:
    """Check if URL points to a binary asset."""
    path = unquote(urlparse(url).path)
    return PurePosixPath(path).suffix.lower() in ASSET_EXTENSIONS


def filter_and_group_urls(urls: list[str]) -> dict:
    """Filter assets and group by site."""
    by_site: dict[str, list[str]] = {}
    assets, unknown = [], []

    for url in urls:
        site_id, path, _ = resolve_url_to_site(url)
        if not site_id:
            unknown.append(url)
        elif is_asset_url(url):
            assets.append({"url": url, "site_id": site_id, "path": path})
        else:
            by_site.setdefault(site_id, []).append(path)

    return {"by_site": by_site, "assets": assets, "unknown": unknown}
```

### Job Tracking

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


def create_job(urls: list[str], by_site: dict, assets: list, unknown: list) -> str:
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "created_at": time.time(),
        "updated_at": time.time(),
        "input": {
            "total_urls": len(urls),
            "to_scrape": sum(len(p) for p in by_site.values()),
            "assets": len(assets),
            "unknown": len(unknown),
            "sites": list(by_site.keys()),
        },
        "progress": {"completed": 0, "success": 0, "skipped": 0, "failed": 0},
        "workers": {"total": 0, "completed": 0},
        "errors": [],
    }
    return job_id


def update_job_progress(job_id: str, result: dict):
    try:
        job = jobs[job_id]
        job["progress"]["completed"] += result.get("success", 0) + result.get("skipped", 0) + result.get("failed", 0)
        job["progress"]["success"] += result.get("success", 0)
        job["progress"]["skipped"] += result.get("skipped", 0)
        job["progress"]["failed"] += result.get("failed", 0)
        job["workers"]["completed"] += 1
        job["updated_at"] = time.time()

        if result.get("errors") and len(job["errors"]) < 20:
            job["errors"].extend(result["errors"][:20 - len(job["errors"])])

        if job["workers"]["completed"] >= job["workers"]["total"]:
            job["status"] = JobStatus.COMPLETED

        jobs[job_id] = job
    except Exception as e:
        print(f"[update_job_progress] Error: {e}")
```

### Batching

```python
def calculate_batches(by_site: dict[str, list[str]], max_containers: int = MAX_CONTAINERS) -> list[dict]:
    """Distribute containers across sites proportionally."""
    if not by_site:
        return []

    total_urls = sum(len(paths) for paths in by_site.values())
    batches = []

    for site_id, paths in by_site.items():
        if not paths:
            continue

        # Proportional allocation (min 1, max len(paths))
        containers = max(1, min(len(paths), round(len(paths) / total_urls * max_containers)))
        batch_size = math.ceil(len(paths) / containers)

        for i in range(0, len(paths), batch_size):
            batches.append({"site_id": site_id, "paths": paths[i:i + batch_size]})

    return batches
```

### SiteWorker

```python
@app.cls(timeout=600, retries=1)
class SiteWorker:
    @modal.enter()
    def start_browser(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch()

    @modal.exit()
    def close_browser(self):
        self.browser.close()
        self.pw.stop()

    @modal.method()
    def process_batch(
        self,
        job_id: str,
        site_id: str,
        paths: list[str],
        delay_ms: int = DEFAULT_DELAY_MS,
        max_age: int = DEFAULT_MAX_AGE,
    ) -> dict:
        config = load_sites_config().get(site_id)
        if not config:
            return {"success": 0, "failed": len(paths), "error": f"Unknown site: {site_id}"}

        content_cfg = config.content
        permissions = ["clipboard-read", "clipboard-write"] if content_cfg.method == "click_copy" else []

        context = self.browser.new_context(user_agent=USER_AGENT, permissions=permissions)
        page = context.new_page()
        results = {"success": 0, "skipped": 0, "failed": 0, "errors": []}

        try:
            for i, path in enumerate(paths):
                cache_key = f"{site_id}:{path}"
                url = config.baseUrl + path

                # Skip if cached
                if get_cached(cache_key, max_age):
                    results["skipped"] += 1
                    continue

                # Skip if error threshold exceeded
                try:
                    err = error_tracker.get(cache_key, {})
                    if err.get("count", 0) >= ERROR_THRESHOLD and time.time() - err.get("timestamp", 0) < ERROR_EXPIRY:
                        results["skipped"] += 1
                        continue
                except KeyError:
                    pass

                try:
                    page.goto(url, wait_until=content_cfg.waitUntil, timeout=content_cfg.gotoTimeoutMs)

                    if wait_for := (content_cfg.waitFor or content_cfg.selector):
                        page.wait_for_selector(wait_for, state="visible", timeout=content_cfg.waitForTimeoutMs)

                    if content_cfg.method == "click_copy":
                        if content_cfg.clickSequence:
                            for step in content_cfg.clickSequence:
                                page.click(step.selector)
                                page.wait_for_timeout(step.waitAfter)
                        else:
                            page.click(content_cfg.selector)
                            page.wait_for_timeout(1000)
                        content = page.evaluate("() => navigator.clipboard.readText()")
                    else:
                        el = page.query_selector(content_cfg.selector)
                        content = html_to_markdown(el.inner_html()) if el else ""

                    if content:
                        set_cached(cache_key, {"content": content, "url": url})
                        results["success"] += 1
                        error_tracker.pop(cache_key, None)
                    else:
                        results["failed"] += 1
                        results["errors"].append({"path": path, "error": "Empty content"})

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({"path": path, "error": str(e)[:200]})
                    try:
                        err = error_tracker.get(cache_key, {})
                        error_tracker[cache_key] = {"count": err.get("count", 0) + 1, "last_error": str(e)[:200], "timestamp": time.time()}
                    except Exception:
                        pass

                if i < len(paths) - 1:
                    time.sleep(delay_ms / 1000)
        finally:
            context.close()

        update_job_progress(job_id, results)
        return results
```

### Endpoints

```python
class BulkScrapeRequest(BaseModel):
    urls: list[str]
    max_age: int = DEFAULT_MAX_AGE


@web_app.post("/jobs/bulk")
async def submit_bulk_job(request: BulkScrapeRequest):
    if not request.urls:
        raise HTTPException(400, "No URLs provided")

    grouped = filter_and_group_urls(request.urls)

    # Cache asset links
    for asset in grouped["assets"]:
        set_cached(f"{asset['site_id']}:{asset['path']}:asset", {"url": asset["url"], "type": "asset"})

    if not grouped["by_site"]:
        return {"job_id": "", "status": "completed", "message": "No scrapeable URLs"}

    job_id = create_job(request.urls, grouped["by_site"], grouped["assets"], grouped["unknown"])
    batches = calculate_batches(grouped["by_site"])

    job = jobs[job_id]
    job["status"] = JobStatus.IN_PROGRESS
    job["workers"]["total"] = len(batches)
    jobs[job_id] = job

    worker = SiteWorker()
    for batch in batches:
        worker.process_batch.spawn(job_id, batch["site_id"], batch["paths"], max_age=request.max_age)

    return {"job_id": job_id, "status": "in_progress", "batches": len(batches), "input": job["input"]}


@web_app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job not found: {job_id}")

    total = job["input"]["to_scrape"]
    pct = round((job["progress"]["completed"] / total) * 100, 1) if total else 100

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress_pct": pct,
        "elapsed_seconds": round(time.time() - job["created_at"], 1),
        "input": job["input"],
        "progress": job["progress"],
        "workers": job["workers"],
        "errors": job["errors"][:10],
    }


@web_app.get("/jobs")
async def list_jobs(limit: int = Query(default=20, le=100)):
    result = []
    for job_id in list(jobs.keys())[-limit:]:
        try:
            job = jobs[job_id]
            result.append({
                "job_id": job_id,
                "status": job["status"],
                "created_at": job["created_at"],
                "sites": job["input"]["sites"],
                "progress": f"{job['progress']['completed']}/{job['input']['to_scrape']}",
            })
        except Exception:
            pass
    return {"jobs": sorted(result, key=lambda x: x["created_at"], reverse=True)}
```

## Usage

```bash
# Submit job
curl -X POST "https://app.modal.run/jobs/bulk" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://clerk.com/docs/auth", "https://stripe.com/docs/api"]}'

# Check status
curl "https://app.modal.run/jobs/a1b2c3d4"

# List jobs
curl "https://app.modal.run/jobs"
```

## Timing

| URLs | Sites | Containers | URLs/Container | Time |
|------|-------|------------|----------------|------|
| 100 | 1 | 10 | 10 | ~15s |
| 500 | 5 | 100 | 5 | ~10s |
| 1000 | 5 | 100 | 10 | ~15s |
| 2000 | 10 | 100 | 20 | ~30s |
# Architecture

Bulk scraping with optimal batching across containers.

## Overview

```
POST /jobs/bulk (1000 URLs)
  → Filter assets (.pdf, .zip) → cache as links
  → Group by site_id
  → Calculate batches (URLs ÷ containers per site)
  → .spawn() workers (fire-and-forget)
  → Return job_id

SiteWorker containers (up to 100)
  → 1 browser per container
  → 1 site per container
  → Sequential scraping, 1s delay between requests
  → Write to cache, update job progress

GET /jobs/{job_id}
  → Check status anytime
```

## Example

1000 URLs: 200 each across 5 sites, 100 containers available.

| Step | Result |
|------|--------|
| Filter | 50 assets cached, 950 to scrape |
| Group | 5 sites × 190 URLs |
| Batch | 100 containers ÷ 5 sites = 20/site, ~10 URLs/container |
| Spawn | 100 workers |
| Time | 10 URLs × 2s ≈ 20 seconds total |

## Implementation

### Constants

```python
MAX_CONTAINERS = 100

ASSET_EXTENSIONS = {
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp4", ".mp3", ".wav", ".webm", ".mov",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".dmg", ".pkg", ".deb", ".rpm",
}

USER_AGENT = "DocPull/1.0 (+https://github.com/yourrepo/docpull) documentation archiver"
DEFAULT_DELAY_MS = 1000

jobs = modal.Dict.from_name("scrape-jobs", create_if_missing=True)
```

### Asset Detection & Grouping

```python
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath


def is_asset_url(url: str) -> bool:
    """Check if URL points to a binary asset."""
    path = unquote(urlparse(url).path)
    return PurePosixPath(path).suffix.lower() in ASSET_EXTENSIONS


def filter_and_group_urls(urls: list[str]) -> dict:
    """Filter assets and group by site."""
    by_site: dict[str, list[str]] = {}
    assets, unknown = [], []

    for url in urls:
        site_id, path, _ = resolve_url_to_site(url)
        if not site_id:
            unknown.append(url)
        elif is_asset_url(url):
            assets.append({"url": url, "site_id": site_id, "path": path})
        else:
            by_site.setdefault(site_id, []).append(path)

    return {"by_site": by_site, "assets": assets, "unknown": unknown}
```

### Job Tracking

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


def create_job(urls: list[str], by_site: dict, assets: list, unknown: list) -> str:
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "created_at": time.time(),
        "updated_at": time.time(),
        "input": {
            "total_urls": len(urls),
            "to_scrape": sum(len(p) for p in by_site.values()),
            "assets": len(assets),
            "unknown": len(unknown),
            "sites": list(by_site.keys()),
        },
        "progress": {"completed": 0, "success": 0, "skipped": 0, "failed": 0},
        "workers": {"total": 0, "completed": 0},
        "errors": [],
    }
    return job_id


def update_job_progress(job_id: str, result: dict):
    try:
        job = jobs[job_id]
        job["progress"]["completed"] += result.get("success", 0) + result.get("skipped", 0) + result.get("failed", 0)
        job["progress"]["success"] += result.get("success", 0)
        job["progress"]["skipped"] += result.get("skipped", 0)
        job["progress"]["failed"] += result.get("failed", 0)
        job["workers"]["completed"] += 1
        job["updated_at"] = time.time()

        if result.get("errors") and len(job["errors"]) < 20:
            job["errors"].extend(result["errors"][:20 - len(job["errors"])])

        if job["workers"]["completed"] >= job["workers"]["total"]:
            job["status"] = JobStatus.COMPLETED

        jobs[job_id] = job
    except Exception as e:
        print(f"[update_job_progress] Error: {e}")
```

### Batching

```python
def calculate_batches(by_site: dict[str, list[str]], max_containers: int = MAX_CONTAINERS) -> list[dict]:
    """Distribute containers across sites proportionally."""
    if not by_site:
        return []

    total_urls = sum(len(paths) for paths in by_site.values())
    batches = []

    for site_id, paths in by_site.items():
        if not paths:
            continue

        # Proportional allocation (min 1, max len(paths))
        containers = max(1, min(len(paths), round(len(paths) / total_urls * max_containers)))
        batch_size = math.ceil(len(paths) / containers)

        for i in range(0, len(paths), batch_size):
            batches.append({"site_id": site_id, "paths": paths[i:i + batch_size]})

    return batches
```

### SiteWorker

```python
@app.cls(timeout=600, retries=1)
class SiteWorker:
    @modal.enter()
    def start_browser(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch()

    @modal.exit()
    def close_browser(self):
        self.browser.close()
        self.pw.stop()

    @modal.method()
    def process_batch(
        self,
        job_id: str,
        site_id: str,
        paths: list[str],
        delay_ms: int = DEFAULT_DELAY_MS,
        max_age: int = DEFAULT_MAX_AGE,
    ) -> dict:
        config = load_sites_config().get(site_id)
        if not config:
            return {"success": 0, "failed": len(paths), "error": f"Unknown site: {site_id}"}

        content_cfg = config.content
        permissions = ["clipboard-read", "clipboard-write"] if content_cfg.method == "click_copy" else []

        context = self.browser.new_context(user_agent=USER_AGENT, permissions=permissions)
        page = context.new_page()
        results = {"success": 0, "skipped": 0, "failed": 0, "errors": []}

        try:
            for i, path in enumerate(paths):
                cache_key = f"{site_id}:{path}"
                url = config.baseUrl + path

                # Skip if cached
                if get_cached(cache_key, max_age):
                    results["skipped"] += 1
                    continue

                # Skip if error threshold exceeded
                try:
                    err = error_tracker.get(cache_key, {})
                    if err.get("count", 0) >= ERROR_THRESHOLD and time.time() - err.get("timestamp", 0) < ERROR_EXPIRY:
                        results["skipped"] += 1
                        continue
                except KeyError:
                    pass

                try:
                    page.goto(url, wait_until=content_cfg.waitUntil, timeout=content_cfg.gotoTimeoutMs)

                    if wait_for := (content_cfg.waitFor or content_cfg.selector):
                        page.wait_for_selector(wait_for, state="visible", timeout=content_cfg.waitForTimeoutMs)

                    if content_cfg.method == "click_copy":
                        if content_cfg.clickSequence:
                            for step in content_cfg.clickSequence:
                                page.click(step.selector)
                                page.wait_for_timeout(step.waitAfter)
                        else:
                            page.click(content_cfg.selector)
                            page.wait_for_timeout(1000)
                        content = page.evaluate("() => navigator.clipboard.readText()")
                    else:
                        el = page.query_selector(content_cfg.selector)
                        content = html_to_markdown(el.inner_html()) if el else ""

                    if content:
                        set_cached(cache_key, {"content": content, "url": url})
                        results["success"] += 1
                        error_tracker.pop(cache_key, None)
                    else:
                        results["failed"] += 1
                        results["errors"].append({"path": path, "error": "Empty content"})

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append({"path": path, "error": str(e)[:200]})
                    try:
                        err = error_tracker.get(cache_key, {})
                        error_tracker[cache_key] = {"count": err.get("count", 0) + 1, "last_error": str(e)[:200], "timestamp": time.time()}
                    except Exception:
                        pass

                if i < len(paths) - 1:
                    time.sleep(delay_ms / 1000)
        finally:
            context.close()

        update_job_progress(job_id, results)
        return results
```

### Endpoints

```python
class BulkScrapeRequest(BaseModel):
    urls: list[str]
    max_age: int = DEFAULT_MAX_AGE


@web_app.post("/jobs/bulk")
async def submit_bulk_job(request: BulkScrapeRequest):
    if not request.urls:
        raise HTTPException(400, "No URLs provided")

    grouped = filter_and_group_urls(request.urls)

    # Cache asset links
    for asset in grouped["assets"]:
        set_cached(f"{asset['site_id']}:{asset['path']}:asset", {"url": asset["url"], "type": "asset"})

    if not grouped["by_site"]:
        return {"job_id": "", "status": "completed", "message": "No scrapeable URLs"}

    job_id = create_job(request.urls, grouped["by_site"], grouped["assets"], grouped["unknown"])
    batches = calculate_batches(grouped["by_site"])

    job = jobs[job_id]
    job["status"] = JobStatus.IN_PROGRESS
    job["workers"]["total"] = len(batches)
    jobs[job_id] = job

    worker = SiteWorker()
    for batch in batches:
        worker.process_batch.spawn(job_id, batch["site_id"], batch["paths"], max_age=request.max_age)

    return {"job_id": job_id, "status": "in_progress", "batches": len(batches), "input": job["input"]}


@web_app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job not found: {job_id}")

    total = job["input"]["to_scrape"]
    pct = round((job["progress"]["completed"] / total) * 100, 1) if total else 100

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress_pct": pct,
        "elapsed_seconds": round(time.time() - job["created_at"], 1),
        "input": job["input"],
        "progress": job["progress"],
        "workers": job["workers"],
        "errors": job["errors"][:10],
    }


@web_app.get("/jobs")
async def list_jobs(limit: int = Query(default=20, le=100)):
    result = []
    for job_id in list(jobs.keys())[-limit:]:
        try:
            job = jobs[job_id]
            result.append({
                "job_id": job_id,
                "status": job["status"],
                "created_at": job["created_at"],
                "sites": job["input"]["sites"],
                "progress": f"{job['progress']['completed']}/{job['input']['to_scrape']}",
            })
        except Exception:
            pass
    return {"jobs": sorted(result, key=lambda x: x["created_at"], reverse=True)}
```

## Usage

```bash
# Submit job
curl -X POST "https://app.modal.run/jobs/bulk" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://clerk.com/docs/auth", "https://stripe.com/docs/api"]}'

# Check status
curl "https://app.modal.run/jobs/a1b2c3d4"

# List jobs
curl "https://app.modal.run/jobs"
```

## Timing

| URLs | Sites | Containers | URLs/Container | Time |
|------|-------|------------|----------------|------|
| 100 | 1 | 10 | 10 | ~15s |
| 500 | 5 | 100 | 5 | ~10s |
| 1000 | 5 | 100 | 10 | ~15s |
| 2000 | 10 | 100 | 20 | ~30s |
