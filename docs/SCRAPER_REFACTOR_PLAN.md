# Scraper Refactor Plan

## Status: Complete

The refactor has been implemented. This document now serves as architecture documentation.

---

## Architecture

```
scraper/
├── config/
│   └── sites.json              # All site definitions
├── extractors/
│   ├── __init__.py             # Extractor base class + registry
│   ├── default.py              # Generic link/content extractors
│   ├── terraform.py            # Terraform-specific (cookie consent, SPA)
│   ├── modal.py                # Modal-specific (click_copy)
│   ├── convex.py               # Convex-specific
│   ├── cursor.py               # Cursor-specific
│   ├── claude_code.py          # Claude Code-specific
│   └── unsloth.py              # Unsloth-specific
├── fetchers.py                 # fetch_html() and browser_page()
├── core.py                     # scrape_links(), scrape_content(), legacy scrape()
├── models.py                   # SiteConfig, ScrapeResult, legacy ScrapeJob
├── extract.py                  # Legacy extraction methods (kept for backwards compat)
├── __init__.py                 # Module exports
└── __main__.py                 # CLI
```

---

## Usage

### CLI

```bash
python -m scraper sites                              # List all available sites
python -m scraper links terraform-aws                # Get all doc links
python -m scraper content terraform-aws /resources/aws_instance
python -m scraper info modal                         # Show site configuration
```

### Python API

```python
from scraper import scrape_links, scrape_content, list_sites

# List available sites
sites = list_sites()  # ['modal', 'convex', 'terraform-aws', ...]

# Get all links for a site
result = await scrape_links("terraform-aws")
print(result.data)  # List of URLs

# Get content from a specific page
result = await scrape_content("modal", "/guide")
print(result.data)  # List of content strings
```

### REST API

```
GET /sites                        # List available site IDs
GET /sites/{site_id}/links        # Get all doc links for a site
GET /sites/{site_id}/content      # Get content from a page
```

---

## Adding a New Site

1. Add site config to `scraper/config/sites.json`:

```json
{
  "new-site": {
    "name": "New Site",
    "baseUrl": "https://docs.example.com",
    "mode": "fetch",
    "extractor": "default",
    "links": {
      "startUrls": [""],
      "pattern": "docs.example.com",
      "maxDepth": 2
    },
    "content": {
      "mode": "browser",
      "waitFor": "#copy-button",
      "selector": "#copy-button",
      "method": "click_copy"
    }
  }
}
```

2. If custom logic is needed, create `scraper/extractors/new_site.py`:

```python
from .default import DefaultExtractor
from . import register

@register("new_site")
class NewSiteExtractor(DefaultExtractor):
    async def setup_browser(self, page):
        # Handle cookie consent, login, etc.
        pass
```

3. Import the new extractor in `scraper/extractors/__init__.py`

---

## Next Steps

- [ ] Add end-to-end tests for each site
- [ ] Add rate limiting to fetchers
- [ ] Add retry logic with exponential backoff
- [ ] Consider caching layer for fetch mode
