# docpull

Modal-based documentation scraper. Fetches docs from various sites and saves locally as markdown.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Or with uv (faster):
uv sync

# Deploy to Modal
python setup.py
```

## Usage

### CLI

```bash
python cli/main.py sites                     # List available sites
python cli/main.py links modal               # Get all doc links
python cli/main.py content modal /guide      # Fetch single page
python cli/main.py index modal               # Bulk fetch entire site
python cli/main.py download modal            # Download site as ZIP

# Bulk jobs (fire-and-forget parallel scraping)
python cli/main.py bulk urls.txt             # Submit job, returns job_id
python cli/main.py job <job_id>              # Check job status
python cli/main.py job <job_id> --watch      # Watch live progress
python cli/main.py jobs                      # List recent jobs
```

### Web UI

After running `python setup.py`, open the UI URL shown in the terminal.

Output: `./docs/<site>/<path>.md`

## Configuration

Site configs in `config/sites.json`. Key fields:

| Field | Description |
|-------|-------------|
| `baseUrl` | Docs root URL |
| `mode` | `fetch` or `browser` |
| `links.startUrls` | Entry points for crawling |
| `links.maxDepth` | Recursion depth (fetch mode only) |
| `links.pattern` | URL filter pattern |
| `content.selector` | CSS/XPath for content extraction |
| `content.method` | `inner_html` or `click_copy` |
| `content.waitUntil` | `domcontentloaded` or `networkidle` |

## REST API

```
GET  /sites                    # List sites
GET  /sites/{id}/links         # Get doc links
GET  /sites/{id}/content       # Get page content
POST /sites/{id}/index         # Bulk fetch (sequential)
GET  /sites/{id}/download      # Download as ZIP

POST /jobs/bulk                # Submit parallel job
GET  /jobs/{job_id}            # Job status
GET  /jobs                     # List jobs

GET  /cache/stats              # Cache stats
DELETE /cache/{id}             # Clear cache
```
