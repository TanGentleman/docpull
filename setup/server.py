#!/usr/bin/env python3
"""FastAPI server for web-based docpull installation."""

import asyncio
import json
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="Docpull Installer")

# Store active deployments
deployments = {}

# Project root is one level up
PROJECT_ROOT = Path(__file__).parent.parent
SETUP_PY = PROJECT_ROOT / "setup.py"
LOGS_DIR = Path(__file__).parent / "logs"
HTML_FILE = Path(__file__).parent / "install.html"


class DeploymentState:
    """Track deployment state and output."""

    def __init__(self, deployment_id: str):
        self.deployment_id = deployment_id
        self.queue = asyncio.Queue()
        self.status = "running"
        self.api_url = None
        self.ui_url = None
        self.error = None
        self.log_file = LOGS_DIR / f"deploy-{deployment_id}.log"

    async def add_line(self, line: str):
        """Add line to queue and log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {line}"

        # Write to log file
        with open(self.log_file, "a") as f:
            f.write(log_line + "\n")

        # Add to queue for streaming
        await self.queue.put(line)


async def run_deployment(state: DeploymentState):
    """Run setup.py and capture output."""
    try:
        # Run setup.py with JSON output flag
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(SETUP_PY),
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(PROJECT_ROOT),
        )

        # Stream output line by line
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break

            line = line_bytes.decode().rstrip()
            if line:
                await state.add_line(line)

        # Wait for process to complete
        await process.wait()

        if process.returncode == 0:
            # Parse JSON output from last line
            # Read the last few lines from log to find JSON
            with open(state.log_file, "r") as f:
                lines = f.readlines()

            # Find JSON output (last non-empty line)
            for line in reversed(lines):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        result = json.loads(line.split("] ", 1)[1])
                        state.api_url = result.get("api_url")
                        state.ui_url = result.get("ui_url")
                        state.status = result.get("status", "success")
                        break
                    except (json.JSONDecodeError, IndexError):
                        continue

            if state.status != "error":
                state.status = "complete"
        else:
            state.status = "error"
            state.error = f"Deployment failed with exit code {process.returncode}"

    except Exception as e:
        state.status = "error"
        state.error = str(e)
        await state.add_line(f"❌ Error: {e}")

    finally:
        # Signal completion
        await state.queue.put(None)


async def stream_generator(deployment_id: str) -> AsyncGenerator[dict, None]:
    """Generate SSE events from deployment queue."""
    state = deployments.get(deployment_id)
    if not state:
        yield {"event": "error", "data": json.dumps({"error": "Deployment not found"})}
        return

    while True:
        line = await state.queue.get()

        if line is None:
            # Deployment complete
            yield {
                "event": "complete",
                "data": json.dumps(
                    {
                        "status": state.status,
                        "api_url": state.api_url,
                        "ui_url": state.ui_url,
                        "error": state.error,
                    }
                ),
            }
            break

        # Stream log line
        yield {"event": "log", "data": json.dumps({"line": line})}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the installation UI."""
    if not HTML_FILE.exists():
        raise HTTPException(status_code=500, detail="install.html not found")
    return FileResponse(HTML_FILE)


@app.post("/deploy")
async def start_deployment():
    """Start a new deployment."""
    # Generate deployment ID
    deployment_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Create deployment state
    state = DeploymentState(deployment_id)
    deployments[deployment_id] = state

    # Start deployment in background
    asyncio.create_task(run_deployment(state))

    return {"deployment_id": deployment_id}


@app.get("/stream/{deployment_id}")
async def stream_logs(deployment_id: str):
    """Stream deployment logs via SSE."""
    return EventSourceResponse(stream_generator(deployment_id))


@app.get("/logs/{deployment_id}")
async def download_log(deployment_id: str):
    """Download deployment log file."""
    state = deployments.get(deployment_id)
    if not state:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if not state.log_file.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    return FileResponse(
        state.log_file,
        media_type="text/plain",
        filename=f"deploy-{deployment_id}.log",
    )


def main():
    """Start the server and open browser."""
    # Ensure logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)

    # Check that setup.py exists
    if not SETUP_PY.exists():
        print(f"❌ Error: setup.py not found at {SETUP_PY}")
        sys.exit(1)

    print("🚀 Starting Docpull Installer Server")
    print("=" * 60)
    print(f"📂 Project root: {PROJECT_ROOT}")
    print(f"🌐 Opening browser to http://localhost:8000")
    print("=" * 60)

    # Open browser after a short delay
    def open_browser():
        import time

        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")

    import threading

    threading.Thread(target=open_browser, daemon=True).start()

    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
