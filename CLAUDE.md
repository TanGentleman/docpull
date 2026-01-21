# CLAUDE.md

Documentation scraper with caching. Fetches docs from various sites and saves locally as markdown.

## docpull CLI

```bash
# List available sites
python docpull.py sites

# Get all doc links for a site
python docpull.py links modal
python docpull.py links modal --force      # Bypass cache (use after changing maxDepth in config)
python docpull.py links modal --save       # Save to ./data/<site>_links.json

# Fetch single page content (cached 1 hour)
python docpull.py content modal /guide
python docpull.py content modal /guide --force   # Bypass cache + clear error tracking

# Bulk fetch entire site (parallel, respects cache)
python docpull.py index modal

# Cache management
python docpull.py cache stats              # View stats by site and type
python docpull.py cache clear modal        # Clear all cache for a site
```

Output saved to `./docs/<site>/<path>.md`

## Key Files

| File | Purpose |
|------|---------|
| `docpull.py` | CLI client |
| `content-scraper-api.py` | Modal API (FastAPI + Playwright) |
| `scraper/config/sites.json` | Site definitions (URLs, selectors, modes) |
| `docs/ARCHITECTURE.md` | Detailed architecture docs |

## Adding a New Site

Add config to `scraper/config/sites.json`:

```json
{
  "new-site": {
    "name": "New Site",
    "baseUrl": "https://docs.example.com",
    "mode": "fetch",
    "links": {
      "startUrls": [""],
      "pattern": "docs.example.com",
      "maxDepth": 2
    },
    "content": {
      "mode": "browser",
      "selector": "#content",
      "method": "inner_html"
    }
  }
}
```

Modes: `fetch` (HTTP crawl) or `browser` (Playwright for JS-heavy sites)

## Dev Commands

```bash
uv sync                                # Install deps
modal serve content-scraper-api.py     # Dev server (hot reload)
modal deploy content-scraper-api.py    # Deploy to Modal
```
