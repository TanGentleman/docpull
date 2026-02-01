# Web-Based Installation UI

A FastAPI-powered web interface for deploying docpull to Modal with real-time progress streaming.

## Quick Start

```bash
# Make sure you're in your virtual environment
cd setup
python server.py
```

This will:
1. Start a local web server at `http://localhost:8000`
2. Automatically open your browser
3. Display the installation UI

## Features

- 🎯 **One-Click Deployment** - Click "Deploy to Modal" and watch the magic happen
- 📺 **Real-Time Streaming** - See deployment progress live in your browser
- 🎨 **Beautiful UI** - Terminal-inspired interface with color-coded output
- 📥 **Log Downloads** - Download deployment logs for debugging
- 🔄 **Retry Support** - Easy retry if deployment fails

## How It Works

1. **Start Server** - Run `python server.py`
2. **Click Deploy** - Browser opens to installation UI
3. **Watch Progress** - Real-time streaming of setup.py output
4. **Get URLs** - Clickable links to deployed API and UI
5. **Done!** - Download logs or deploy again

## Architecture

```
setup/
├── server.py          # FastAPI server with SSE streaming
├── install.html       # Web UI with real-time console
└── logs/              # Deployment logs (auto-generated)
    └── deploy-*.log
```

## Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sse-starlette` - Server-Sent Events for streaming

These are already in your project's requirements.txt.

## Output Format

The server streams deployment output in real-time using Server-Sent Events (SSE). Logs are also saved to `logs/deploy-{timestamp}.log` for later review.

## Traditional CLI

Prefer the command line? You can still use:

```bash
cd ..
python setup.py
```

The web UI just provides a nicer experience with visual feedback.
