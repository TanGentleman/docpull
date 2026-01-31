# Docpull UI

Web interface for managing documentation scraping.

## Files

- `server.py` - Local development server (runs CLI commands via subprocess)
- `app.py` - Modal-deployed version (proxies to scraper API)
- `ui.html` - Shared HTML/JS frontend

## Local Development

### Prerequisites

```bash
pip install fastapi uvicorn httpx
```

### Run

From the project root:

```bash
python ui/server.py
```

Or from the `ui/` directory:

```bash
cd ui
python server.py
```

Open http://127.0.0.1:8080

### Features (Local)

1. **Discover** - Analyze a docs page and get suggested config
2. **Edit Configuration** - Modify and save to `sites.json`
3. **Fetch Links** - Test link discovery for a site
4. **Scrape Content** - Test content extraction
5. **Export URLs** - Download docs as ZIP

## Deploy to Modal

From the project root:

```bash
modal deploy ui/app.py
```

### Features (Deployed)

The deployed version has the same UI but limited functionality:
- Discover, Links, Content, Export all work
- Adding sites is disabled (no filesystem access)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | `dev` or `prod` | `dev` |
| `MODAL_USERNAME` | Modal username for API URL | `tangentleman` |
| `MODAL_KEY` | Modal auth key (optional) | - |
| `MODAL_SECRET` | Modal auth secret (optional) | - |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve UI |
| `/api/sites` | GET | List configured sites |
| `/api/discover` | POST | Analyze a URL |
| `/api/add-site` | POST | Add site config (local only) |
| `/api/links` | POST | Get links for a site |
| `/api/content` | POST | Get content for a page |
| `/api/export` | POST | Export URLs as ZIP |
