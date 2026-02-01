# Installation Guide

## Quick Install

```bash
./install
```

This will:
1. Set up a virtual environment (using `uv` if available, otherwise standard Python venv)
2. Install all dependencies from requirements.txt
3. Verify Modal authentication
4. Deploy the API and UI to Modal

## Requirements

- Python 3.12+ (as specified in pyproject.toml)
- A Modal account (sign up at https://modal.com)

## Installation Methods

### Method 1: Automated Script (Recommended)

```bash
./install
```

The install script automatically detects and uses:
- **uv** (if installed) - Fast Rust-based package installer
- **python3 venv** (fallback) - Standard Python virtual environment

### Method 2: Manual Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Authenticate with Modal
modal token set

# Deploy
python setup.py
```

### Method 3: With uv (Fast)

```bash
# Install uv first: https://github.com/astral-sh/uv
uv sync
source .venv/bin/activate
modal token set
python setup.py
```

## Modal Authentication

The install script will check if you're authenticated with Modal. If not, you'll be prompted to run:

```bash
modal token set
```

This opens a browser window to authenticate with your Modal account.

## What Gets Deployed

After installation, you'll have:

1. **API** - Content scraper API deployed to Modal
2. **UI** - Web interface deployed to Modal
3. **CLI** - Local command-line tool (`python cli/main.py`)

## Post-Installation

### Use the Web UI

```bash
source .venv/bin/activate
cd setup
python server.py
```

This starts a local web server with a beautiful deployment interface.

### Use the CLI

```bash
source .venv/bin/activate
python cli/main.py sites        # List available sites
python cli/main.py links <url>  # Get documentation links
python cli/main.py content <url> # Fetch content as markdown
```

### Redeploy Changes

```bash
source .venv/bin/activate
python setup.py
```

## Uninstallation

```bash
./uninstall  # Coming soon!
```

For now, manually clean up:

```bash
# List Modal deployments
modal app list

# Delete specific app
modal app delete <app-name>

# Remove local files
rm -rf .venv
rm -f ui/config.py
rm -rf setup/logs/
```

## Troubleshooting

### "Not running in a virtual environment"

Make sure to activate the venv:
```bash
source .venv/bin/activate
```

### "Modal not authenticated"

Run:
```bash
modal token set
```

### "Python 3.12+ required"

Check your Python version:
```bash
python3 --version
```

Install Python 3.12+ if needed, then run `./install` again.

### Missing dependencies

The install script should handle this, but if needed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Development Workflow

See [CLAUDE.md](./CLAUDE.md) for development instructions, including:
- Adding new documentation sites
- Local testing with hot-reload
- Configuration changes
