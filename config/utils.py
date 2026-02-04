"""Central configuration for docpull.

Reads configuration from environment variables, with .env file support.
Run 'python deploy.py' to auto-generate .env after deployment.

Environment variables:
- SCRAPER_API_URL: The Modal API URL (required)
- ACCESS_KEY: API access key for authentication (optional)
"""

import os
from pathlib import Path

# Load .env file from project root if it exists
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except (ImportError, PermissionError, OSError):
    pass  # dotenv not installed or .env not accessible, rely on environment variables

# Configuration values
SCRAPER_API_URL: str | None = os.environ.get("SCRAPER_API_URL")
ACCESS_KEY: str | None = os.environ.get("ACCESS_KEY")


def get_api_url() -> str:
    """Get the configured API URL.

    Returns:
        str: The API URL

    Raises:
        RuntimeError: If the API URL is not configured
    """
    if not SCRAPER_API_URL:
        raise RuntimeError(
            "SCRAPER_API_URL is not configured.\n"
            "Either:\n"
            "  1. Run 'python deploy.py' to deploy and auto-configure, or\n"
            "  2. Set SCRAPER_API_URL in .env or as an environment variable"
        )
    return SCRAPER_API_URL


def get_auth_headers() -> dict:
    """Get authentication headers if configured.

    Returns:
        dict: Headers with X-Access-Key if ACCESS_KEY is set, empty dict otherwise
    """
    if ACCESS_KEY:
        return {"X-Access-Key": ACCESS_KEY}
    return {}
