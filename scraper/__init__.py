"""Scraper module - stateless scraping with pluggable extraction."""

# New API
from .models import ScrapeResult, SiteConfig, Mode, Operation
from .core import scrape_links, scrape_content, load_site_config, list_sites
from .extractors import Extractor, get_extractor, EXTRACTORS as EXTRACTOR_REGISTRY
from .fetchers import fetch_html, fetch_all_html, browser_page, browser_context

# Legacy API (backwards compatibility)
from .models import ScrapeJob, LegacyScrapeResult as ScrapeResult_Legacy, ExtractFn, ParseFn
from .extract import click_copy, text_content, inner_html, terraform_links, EXTRACTORS
from .core import scrape, scrape_batch

# Re-export ScrapeResult under legacy name for backwards compatibility
# Note: ScrapeResult is now the new model, use ScrapeResult_Legacy for old code

__all__ = [
    # New API - Models
    "ScrapeResult",
    "SiteConfig",
    "Mode",
    "Operation",
    # New API - Core functions
    "scrape_links",
    "scrape_content",
    "load_site_config",
    "list_sites",
    # New API - Extractors
    "Extractor",
    "get_extractor",
    "EXTRACTOR_REGISTRY",
    # New API - Fetchers
    "fetch_html",
    "fetch_all_html",
    "browser_page",
    "browser_context",
    # Legacy API - Types
    "ScrapeJob",
    "ScrapeResult_Legacy",
    "ExtractFn",
    "ParseFn",
    # Legacy API - Extractors
    "click_copy",
    "text_content",
    "inner_html",
    "terraform_links",
    "EXTRACTORS",
    # Legacy API - Core
    "scrape",
    "scrape_batch",
]
