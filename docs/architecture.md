# Bulk Job Architecture

Parallel scraping with fire-and-forget workers.

## Flow

```
POST /jobs/bulk
  │
  ├─▶ filter_and_group_urls()  → Group by site, filter assets
  ├─▶ calculate_batches()      → Distribute across containers
  ├─▶ SiteWorker.spawn()       → Fire-and-forget (up to 100)
  └─▶ Return job_id immediately

SiteWorker (per container)
  │
  ├─▶ Browser lifecycle (@modal.enter/@modal.exit)
  ├─▶ Process batch sequentially (1s delay)
  └─▶ update_job_progress() via modal.Dict

GET /jobs/{job_id}
  └─▶ Read progress from modal.Dict
```

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `jobs` Dict | `scraper/bulk.py` | Cross-worker job state |
| `SiteWorker` | `content-scraper-api.py` | Browser lifecycle + batch processing |
| `calculate_batches()` | `scraper/bulk.py` | Proportional container allocation |

## Modal Patterns Used

| Pattern | Docs |
|---------|------|
| Distributed Dict | `docs/modal/guide_dicts.md` |
| Container lifecycle | `docs/modal/guide_lifecycle-functions.md` |
| Fire-and-forget `.spawn()` | `docs/modal/guide_job-queue.md` |
| Input concurrency | `docs/modal/guide_concurrent-inputs.md` |

## Extending

**Add queue-based processing:** See `docs/modal/guide_queues.md` for `modal.Queue` patterns.

**GPU workers:** See `docs/modal/guide_gpu.md` for adding GPU-accelerated extraction.

**Persistent storage:** See `docs/modal/guide_volumes.md` for `modal.Volume` instead of Dict.
