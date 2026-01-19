# handy-apis

Simple Modal-based API endpoints for web automation and scraping.

Draws heavily from: https://github.com/modal-labs/modal-examples

## Quick Start

```bash
# install deps
uv sync

# deploy to modal
modal deploy content-scraper-api.py

# or test locally
modal serve content-scraper-api.py
```

## Scraper Module

A modular scraper with support for multiple documentation sites.

### CLI

```bash
python -m scraper sites                              # List all available sites
python -m scraper links terraform-aws                # Get all doc links
python -m scraper content terraform-aws /resources/aws_instance
python -m scraper info modal                         # Show site configuration
```

### Supported Sites

| Site | Mode | Description |
|------|------|-------------|
| `modal` | fetch | Modal documentation |
| `convex` | fetch | Convex documentation |
| `terraform-aws` | browser | Terraform AWS provider docs |
| `cursor` | fetch | Cursor documentation |
| `claude-code` | fetch | Claude Code documentation |
| `unsloth` | fetch | Unsloth documentation |

### Python API

```python
from scraper import scrape_links, scrape_content, list_sites

# List available sites
sites = list_sites()

# Get all links for a site
result = await scrape_links("terraform-aws")

# Get content from a specific page
result = await scrape_content("modal", "/guide")
```

## REST API

Deploy `content-scraper-api.py` to get these endpoints:

```
GET  /sites                        # List available site IDs
GET  /sites/{site_id}/links        # Get all doc links for a site
GET  /sites/{site_id}/content      # Get content from a page

# Legacy endpoints
GET  /docs/{site_id}/{page}        # Get doc (cached or fresh scrape)
POST /scrape                       # Scrape any URL (stateless)
```

## GitHub Actions

There's a workflow for batch scraping that saves results to `docs/`.

**Setup**: add these secrets to your repo (Settings → Secrets and variables → Actions):
- `MODAL_USERNAME`: your username from `https://[your-username]--{project-name}.modal.run/`
- `MODAL_KEY`: proxy auth token ID (starts with `wk-`)
- `MODAL_SECRET`: proxy auth token secret (starts with `ws-`)

## Architecture

See [docs/SCRAPER_REFACTOR_PLAN.md](docs/SCRAPER_REFACTOR_PLAN.md) for detailed architecture documentation.
