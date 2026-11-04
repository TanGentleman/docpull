# Architecture

Docpull uses a single Modal app with separated concerns: a lightweight API server and a heavyweight Playwright worker.

## Components

```mermaid
flowchart LR
    CLI["docpull CLI<br/><i>cli/main.py</i>"]
    UI["Web UI<br/><i>ui/ui.html</i>"]

    subgraph APP["Modal App (--app-name)"]
        direction LR
        subgraph API["api_image · lightweight"]
            SERVER["FastAPI server<br/><i>api/server.py</i><br/>endpoints · UI · auth<br/>cache · errors · jobs<br/>HTTP link scraping"]
        end
        subgraph PW["playwright_image · Chromium"]
            WORKER["PlaywrightWorker<br/><i>api/worker.py</i><br/>scrape_content · scrape_links<br/>discover_selectors · process_batch"]
        end
        subgraph STORE["Modal Dicts"]
            CACHE[("scraper-cache")]
            ERRORS[("scraper-errors")]
            SITES[("scraper-sites")]
        end
    end

    DOCS["Docs sites"]

    CLI -- "HTTP + X-Access-Key" --> SERVER
    UI --> SERVER
    SERVER -- ".remote() / .spawn()" --> WORKER
    SERVER <--> CACHE
    SERVER <--> ERRORS
    SERVER <--> SITES
    WORKER -- "batch results" --> CACHE
    WORKER -- "headless browser" --> DOCS
    SERVER -- "httpx (no browser)" --> DOCS

    classDef client fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef api fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef worker fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef store fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef ext fill:#f1f5f9,stroke:#64748b,color:#0f172a
    class CLI,UI client
    class SERVER api
    class WORKER worker
    class CACHE,ERRORS,SITES store
    class DOCS ext
    style APP fill:#f8fafc,stroke:#94a3b8
    style API fill:#f0fdf4,stroke:#86efac
    style PW fill:#fffbeb,stroke:#fcd34d
    style STORE fill:#f5f3ff,stroke:#c4b5fd
```

## Images

### api_image (lightweight)
- Base: `debian_slim`
- Packages: `fastapi`, `pydantic`, `httpx`, `markdownify`
- Purpose: Serve API endpoints and static UI

### playwright_image (heavyweight)
- Base: `debian_slim` + Chromium
- Packages: `playwright`, `markdownify`, `httpx`
- Purpose: Browser-based scraping

## Data Flow

### Single Page Scrape
```mermaid
sequenceDiagram
    participant C as Client
    participant S as server.py
    participant D as scraper-cache
    participant W as PlaywrightWorker
    C->>S: GET /sites/{id}/content?path=...
    S->>D: lookup (max_age)
    alt cache hit
        D-->>S: cached markdown
    else cache miss
        S->>W: scrape_content.remote()
        W-->>S: markdown
        S->>D: store
    end
    S-->>C: markdown
```

### Bulk Scrape (fire-and-forget)
```mermaid
sequenceDiagram
    participant C as Client
    participant S as server.py
    participant W as PlaywrightWorker (xN)
    participant D as scraper-cache
    C->>S: POST /jobs/bulk
    S->>W: process_batch.spawn() per batch
    S-->>C: job_id (immediately)
    W->>D: write each page
    C->>S: GET /jobs/{job_id}
    S-->>C: progress
```

### HTTP Link Discovery (no browser)
```mermaid
flowchart LR
    C[Client] --> S["server.py<br/>scrape_links_fetch()"] --> D[(scraper-cache)] --> C
```

## Files

| File | Purpose |
|------|---------|
| `api/server.py` | FastAPI app, endpoints, cache/error management, UI serving |
| `api/worker.py` | PlaywrightWorkerBase class with browser methods |
| `api/bulk.py` | Job status tracking, batch calculations |
| `api/urls.py` | URL normalization and validation |
| `ui/ui.html` | Web UI (served at `/`) |
| `cli/main.py` | Typer CLI |
| `config/sites.json` | Site configurations |

## Key Design Decisions

1. **Single Modal App**: Server and worker share one app, simplifying deployment and allowing the server to call worker methods directly.

2. **Separated Images**: The API server uses a minimal image without Playwright. Browser work is dispatched to the worker class, which has its own heavyweight image with Chromium.

3. **Fire-and-forget Batches**: Bulk jobs use `.spawn()` so the server returns immediately. The worker writes results directly to the cache.

4. **Config Passed to Workers**: Workers receive full site config dicts in each call. They never read `sites.json` directly, making them stateless and testable.

5. **Inline HTTP Scraping**: Simple HTTP-based link discovery runs inline in the server (no separate Modal function), reducing latency for non-JS sites.
