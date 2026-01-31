# Docpull UI

Web interface for managing documentation scraping.

![Dark theme UI with collapsible cards]

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn httpx

# Run locally
python ui/server.py

# Open http://127.0.0.1:8080
```

## Features

### Your Sites
- Auto-loads all configured sites on page open
- Click any site card to select it across all dropdowns
- Visual grid with hover effects and selection state

### Quick Actions
- **View Links** - Fetch all documentation links for a site
- **Preview Content** - Test content extraction on a specific path
- **Export Site** - One-click export of all cached URLs as ZIP

### Add New Site
- Discover URL analyzer suggests configuration
- JSON editor with live validation
- Auto-fills site ID from hostname

### Export URLs
- Load cached URLs from any site
- Paste custom URL lists
- Option to scrape missing content

## Files

| File | Description |
|------|-------------|
| `server.py` | Local dev server (subprocess CLI calls) |
| `app.py` | Modal deployment (API proxy) |
| `ui.html` | Shared frontend (single HTML file) |

## Local vs Deployed

| Feature | Local | Modal |
|---------|-------|-------|
| View sites | Yes | Yes |
| Discover URLs | Yes | Yes |
| Add new sites | Yes | No* |
| View links | Yes | Yes |
| Preview content | Yes | Yes |
| Export as ZIP | Yes | Yes |

*Adding sites requires filesystem access to `sites.json`

## Deploy to Modal

```bash
modal deploy ui/app.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | `dev` or `prod` | `dev` |
| `MODAL_USERNAME` | Modal username | `tangentleman` |
| `MODAL_KEY` | Auth key (optional) | - |
| `MODAL_SECRET` | Auth secret (optional) | - |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve UI |
| `/api/sites` | GET | List configured sites |
| `/api/discover` | POST | Analyze a URL |
| `/api/add-site` | POST | Add site config |
| `/api/links` | POST | Get links for a site |
| `/api/content` | POST | Get page content |
| `/api/cache/keys` | GET | List cached URLs |
| `/api/export` | POST | Export URLs as ZIP |

## UI Components

The interface uses collapsible cards with state persistence:

```
┌─────────────────────────────────────────┐
│  Docpull                    [N sites]   │
├─────────────────────────────────────────┤
│  ▼ Your Sites                           │
│    [site1] [site2] [site3] [+ Add]      │
├─────────────────────────────────────────┤
│  ▼ Quick Actions                        │
│    Site: [▼]  Path: [____]              │
│    [Links] [Content] [Export]           │
├─────────────────────────────────────────┤
│  ▶ Add New Site (collapsed)             │
├─────────────────────────────────────────┤
│  ▼ Export URLs                          │
│    Load from: [▼] [Load]                │
│    [URLs...]  [Export ZIP]              │
└─────────────────────────────────────────┘
```

Card collapse states are saved to localStorage.
