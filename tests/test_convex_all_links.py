"""Test script for extracting all Convex doc links via Modal API."""

import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

SCRAPER_API = "https://tangentleman--content-scraper-api-fastapi-app-dev.modal.run"
CONVEX_DOCS_BASE = "https://docs.convex.dev"

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_PATH = ROOT_DIR / "data" / "convex_links.json"


def get_auth_headers() -> dict:
    """Get Modal auth headers from environment variables."""
    key = os.environ.get("MODAL_KEY")
    secret = os.environ.get("MODAL_SECRET")
    if key and secret:
        return {"Modal-Key": key, "Modal-Secret": secret}
    return {}


async def get_convex_links() -> list[str]:
    """Extract all documentation links from Convex docs via Modal API."""
    print(f"Calling Modal API: {SCRAPER_API}")
    print(f"Target URL: {CONVEX_DOCS_BASE}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(
            f"{SCRAPER_API}/sites/convex/links",
            headers=get_auth_headers(),
        )

        print(f"Response status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            return []

        data = resp.json()
        links = data.get("links", [])
        count = data.get("count", len(links))
        site_id = data.get("site_id")
        print(f"Site: {site_id}, links returned: {count}")

        if not links:
            print("No links returned")
            return []

        print(f"Found {len(links)} links")
        return links


def main() -> int:
    print("=" * 60)
    print("Extracting Convex Doc Links via Modal API")
    print("=" * 60)
    print()

    links = asyncio.run(get_convex_links())

    if links:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump({"convex_links": links}, f, indent=2)
        print(f"\nSaved {len(links)} links to {OUTPUT_PATH}")

        print("\n--- First 20 links ---")
        for link in links[:20]:
            print(f"  {link}")
        if len(links) > 20:
            print(f"  ... and {len(links) - 20} more")
    else:
        print("\nNo links found!")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

