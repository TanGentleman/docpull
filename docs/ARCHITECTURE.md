# Documentation Scraper Architecture

A Modal-based system for fetching and caching documentation from multiple sites.

## Goals

1. **Discover documentation links** - Crawl a site to find all doc pages.
2. **Scrape content on demand** - Fetch and save docs as local `.md` files via CLI.
3. **Keep the API simple** - One FastAPI app with Modal-native caching and Playwright.

## System Overview

```
┌──────────────────┐         ┌─────────────────────────────────┐
│   docpull.py     │ ──────▶ │   content-scraper-api (Modal)   │
│   (CLI client)   │         │   FastAPI + Playwright          │
└──────────────────┘         └───────────────┬─────────────────┘
                                             │
                             ┌───────────────┴───────────────┐
                             ▼                               ▼
             ┌─────────────────────────┐     ┌─────────────────────────┐
             │   modal.Dict (cache)    │     │   modal.Dict (errors)   │
             │   - Content & links     │     │   - Failed link tracker │
             │   - 7-day TTL           │     │   - 24h auto-expiry     │
             └─────────────────────────┘     └─────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `docpull.py` | CLI client - the main interface for users |
| `content-scraper-api.py` | Modal API - FastAPI + Playwright + cache |
| `scraper/config/sites.json` | Site definitions (URLs, selectors, modes) |

## Link Discovery Flow

1. CLI calls `GET /sites/{site_id}/links`
2. API loads site config from `scraper/config/sites.json`
3. If `mode: "fetch"`: HTTP crawl from `startUrls`, follow links matching `pattern`
4. If `mode: "browser"`: Playwright renders JS and extracts links
5. API returns a deduplicated list of URLs

## Content Scraping Flow

1. CLI calls `GET /sites/{site_id}/content?path=/guide/example`
2. API checks Modal Dict cache (respects `max_age`)
3. If stale/missing: Playwright loads the page and extracts content
4. API stores `{content, url, timestamp}` in the cache
5. CLI writes to `./docs/{site_id}/{path}.md`

## Bulk Indexing

For fetching an entire site at once:

1. CLI calls `POST /sites/{site_id}/index`
2. API fetches all links for the site (cached)
3. Checks cache for each path, separates fresh vs stale
4. Scrapes stale/missing paths in parallel (50 concurrent by default)
5. Returns summary: total, cached, scraped, successful, failed

## Error Tracking

Links that fail repeatedly are automatically skipped to avoid wasting resources:

- **Threshold**: After 3 consecutive failures, a link is skipped
- **Auto-expiry**: Errors expire after 24 hours (auto-recovery)
- **Force override**: Using `--force` clears error tracking for that path
- **Storage**: Errors stored in separate Modal Dict (`scraper-errors`)

Error data: `{count, last_error, timestamp}`

## Cache Behavior

### Content Cache
- **Key format**: `{site_id}:{path}` (e.g., `modal:/guide`)
- **TTL**: 1 hour by default
- **Force refresh**: Use `--force` flag to bypass cache

### Links Cache
- **Key format**: `{site_id}:links` (e.g., `modal:links`)
- **TTL**: 1 hour by default
- **Force refresh**: Use `--force` flag to bypass cache

**Important**: The links cache key does not include config values like `maxDepth`. If you
change `maxDepth` in `sites.json` and want to re-crawl with the new depth, use `--force`
or clear the cache for that site.

## Cache Observability

The API provides cache inspection endpoints:

- `GET /cache/stats` - Total entries, breakdown by site and type
- `DELETE /cache/{site_id}` - Clear all cache for a site

## Site Configuration

All per-site behavior lives in `scraper/config/sites.json`.

Key fields:
- `baseUrl`: Base URL of the docs site
- `mode`: `fetch` or `browser`
- `links`: `startUrls`, `pattern`, `maxDepth`, `waitFor`
- `content`: `selector`, `method`, `waitFor`

### Site-Specific Browser Settings

For JS-heavy sites, navigation timing can differ. The scraper supports optional
Playwright overrides per site:

```json
{
  "content": {
    "waitUntil": "domcontentloaded",
    "gotoTimeoutMs": 20000
  },
  "links": {
    "waitUntil": "domcontentloaded",
    "gotoTimeoutMs": 20000
  }
}
```

Defaults are `waitUntil: "networkidle"` and `gotoTimeoutMs: 20000`. Use
`domcontentloaded` when `networkidle` is too strict (e.g., Terraform docs).

## Development

```bash
uv sync
modal serve content-scraper-api.py
SCRAPER_API_URL=http://localhost:8000 python docpull.py links modal
```

## Tests & Utilities

- `tests/test_terraform_all_links.py` - browser link scrape
- `tests/test_terraform_markdown.py` - HTML → markdown conversion
- `tests/test_convex_all_links.py` - fetch link scrape

## Adding a New Site

1. Add the site definition to `scraper/config/sites.json`.
2. Start the dev server: `modal serve content-scraper-api.py`
3. Validate with `docpull.py` or the test scripts.
