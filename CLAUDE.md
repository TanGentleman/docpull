# CLAUDE.md

Modal-based documentation scraper.

## Project Structure

```
docpull/
├── api/                    # Modal API
│   ├── scraper.py         # FastAPI endpoints
│   ├── bulk.py            # Bulk job handling
│   └── urls.py            # URL utilities
├── cli/main.py            # Typer CLI
├── config/
│   ├── sites.json         # Site definitions
│   └── utils.py           # Env loading
├── ui/app.py              # Gradio UI
├── setup.py               # Deploy script
└── teardown.py            # Stop deployments
```

## Development

```bash
modal serve api/scraper.py   # API with hot-reload
modal serve ui/app.py        # UI with hot-reload
python setup.py              # Deploy both
```

## Adding Sites

1. `docpull discover <url>` to generate config
2. Add to `config/sites.json`
3. Test: `docpull links <id>` and `docpull content <id> <path>`
4. Use `--force` to bypass cache when testing
