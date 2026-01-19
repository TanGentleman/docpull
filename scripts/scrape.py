import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


def validate_api_url() -> str:
    """Validate API URL and return it with the correct suffix."""
    required = ["MODAL_USERNAME", "MODAL_KEY", "MODAL_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    env = os.environ.get("ENVIRONMENT", "prod")
    url_suffix = "-dev" if env == "dev" else ""
    return f"https://{os.environ['MODAL_USERNAME']}--content-scraper-api-fastapi-app{url_suffix}.modal.run"


def get_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Modal-Key": os.environ.get("MODAL_KEY"),
        "Modal-Secret": os.environ.get("MODAL_SECRET"),
    }


@dataclass
class SiteInfo:
    """Site metadata from local config."""
    site_id: str
    name: str
    base_url: str


def load_sites_data() -> Dict[str, dict]:
    """Load site configs from the scraper config JSON."""
    config_path = Path(__file__).parent.parent / "scraper" / "config" / "sites.json"
    with open(config_path) as f:
        data = json.load(f)
    return data.get("sites", {})


def get_site_info(site_id: str) -> SiteInfo:
    """Get site metadata for a given site ID."""
    sites = load_sites_data()
    if site_id not in sites:
        raise ValueError(f"Site '{site_id}' not found")
    site = sites[site_id]
    return SiteInfo(site_id=site_id, name=site["name"], base_url=site["baseUrl"])


def get_available_sites() -> List[str]:
    """Get list of all available site IDs."""
    sites = load_sites_data()
    return list(sites.keys())


def get_site_links(base_url: str, site_id: str) -> List[str]:
    """Fetch all documentation links for a site from the API."""
    resp = requests.get(f"{base_url}/sites/{site_id}/links", headers=get_headers())
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch links for {site_id}: {resp.text}")
    data = resp.json()
    return data.get("links", [])


def link_to_path(link: str, base_url: str) -> str:
    """Convert a full URL to a path relative to the site baseUrl."""
    if link.startswith(base_url):
        suffix = link[len(base_url):]
        if suffix and not suffix.startswith("/"):
            suffix = "/" + suffix
        return suffix
    parsed = urlparse(link)
    return parsed.path or ""


def fetch_content(base_url: str, site_id: str, path: str) -> str:
    """Fetch content for a given site and path."""
    resp = requests.get(
        f"{base_url}/sites/{site_id}/content",
        headers=get_headers(),
        params={"path": path},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch content for {site_id}{path}: {resp.text}")
    data = resp.json()
    return data.get("content", "")


def batch_scrape(
    sites_list: Optional[List[str]] = None,
    use_cache: bool = True,
    verbose: bool = True,
    max_pages: Optional[int] = None,
) -> Dict[str, Dict[str, str]]:
    """Scrape pages via the new /sites endpoints and return docs by site/path."""
    load_dotenv()

    base_url = validate_api_url()
    env = os.environ.get("ENVIRONMENT", "prod")

    if verbose:
        print(f"Using environment: {env}")
        print(f"API URL: {base_url}")
        if use_cache is not None:
            print(f"Cache enabled: {use_cache} (not used by /sites endpoints)")

    target_sites = sites_list or get_available_sites()
    docs: Dict[str, Dict[str, str]] = {}

    for site_id in target_sites:
        site_info = get_site_info(site_id)
        if verbose:
            print(f"\nFetching links for {site_id}...")

        links = get_site_links(base_url, site_id)
        if max_pages is not None:
            links = links[:max_pages]

        if verbose:
            print(f"Found {len(links)} links for {site_id}")

        for link in links:
            path = link_to_path(link, site_info.base_url)
            page_key = path.lstrip("/") or "root"
            try:
                content = fetch_content(base_url, site_id, path)
            except Exception as exc:
                content = ""
                if verbose:
                    print(f"  Failed {site_id}/{page_key}: {exc}")
            docs.setdefault(site_id, {})[page_key] = content
            if verbose:
                print(f"  {site_id}/{page_key}: {len(content)} chars")

    return docs
