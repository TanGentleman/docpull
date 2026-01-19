"""Core scraping functionality."""

import asyncio
import json
from pathlib import Path

from .models import ScrapeResult, SiteConfig, ScrapeJob, LegacyScrapeResult, ExtractFn, ParseFn
from .extractors import get_extractor
from .fetchers import fetch_html, browser_page

# Config path
CONFIG_PATH = Path(__file__).parent / "config" / "sites.json"


def load_site_config(site_id: str) -> SiteConfig:
    """Load site configuration from JSON."""
    with open(CONFIG_PATH) as f:
        data = json.load(f)

    if site_id not in data["sites"]:
        available = list(data["sites"].keys())
        raise ValueError(f"Unknown site: {site_id}. Available: {available}")

    site_data = data["sites"][site_id]
    return SiteConfig(**site_data)


def list_sites() -> list[str]:
    """List all available site IDs."""
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    return list(data["sites"].keys())


async def scrape_links(site_id: str) -> ScrapeResult:
    """
    Get all documentation links for a site.

    Args:
        site_id: Site identifier (e.g., "modal", "terraform-aws")

    Returns:
        ScrapeResult with list of discovered URLs
    """
    try:
        config = load_site_config(site_id)
        extractor = get_extractor(config.extractor)

        if not config.links:
            return ScrapeResult(
                site=site_id,
                operation="links",
                success=False,
                data=[],
                error="Site has no links configuration",
            )

        links_config = config.links.model_dump()
        links_config["baseUrl"] = config.baseUrl

        all_links: set[str] = set()

        if config.mode == "fetch":
            # HTTP fetch mode: crawl starting URLs
            start_urls = [
                config.baseUrl + path if path else config.baseUrl
                for path in config.links.startUrls
            ]

            visited: set[str] = set()
            to_visit = [(url, 0) for url in start_urls]
            max_depth = config.links.maxDepth

            while to_visit:
                batch = []
                while to_visit and len(batch) < 10:
                    url, depth = to_visit.pop(0)
                    if url not in visited and depth <= max_depth:
                        visited.add(url)
                        batch.append((url, depth))

                if not batch:
                    continue

                # Fetch all URLs in batch concurrently
                tasks = [fetch_html(url) for url, _ in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for (url, depth), result in zip(batch, results):
                    if isinstance(result, Exception):
                        print(f"Error fetching {url}: {result}")
                        continue

                    # Extract links from HTML
                    links = await extractor.extract_links(result, links_config)

                    for link in links:
                        all_links.add(link)
                        if depth < max_depth and link not in visited:
                            to_visit.append((link, depth + 1))

        else:
            # Browser mode: use Playwright
            start_url = config.baseUrl + (config.links.startUrls[0] if config.links.startUrls else "")
            wait_for = config.links.waitFor

            async with browser_page(start_url, wait_for=wait_for) as page:
                await extractor.setup_browser(page)
                links = await extractor.extract_links(page, links_config)
                all_links.update(links)

        print(f"Found {len(all_links)} links for {site_id}")
        return ScrapeResult(
            site=site_id,
            operation="links",
            success=True,
            data=sorted(all_links),
        )

    except Exception as e:
        print(f"Error scraping links for {site_id}: {e}")
        return ScrapeResult(
            site=site_id,
            operation="links",
            success=False,
            data=[],
            error=str(e),
        )


async def scrape_content(site_id: str, path: str = "") -> ScrapeResult:
    """
    Get content from a specific page.

    Args:
        site_id: Site identifier (e.g., "modal", "terraform-aws")
        path: Page path relative to baseUrl

    Returns:
        ScrapeResult with extracted content
    """
    try:
        config = load_site_config(site_id)
        extractor = get_extractor(config.extractor)

        if not config.content:
            return ScrapeResult(
                site=site_id,
                operation="content",
                success=False,
                data=[],
                error="Site has no content configuration",
            )

        url = config.baseUrl + path
        content_config = config.content.model_dump()
        content_config["baseUrl"] = config.baseUrl

        # Determine mode (content config can override site mode)
        mode = config.content.mode or config.mode

        if mode == "fetch":
            # HTTP fetch mode
            html = await fetch_html(url)
            content = await extractor.extract_content(html, content_config)
        else:
            # Browser mode
            permissions = []
            if config.content.method == "click_copy":
                permissions = ["clipboard-read", "clipboard-write"]

            async with browser_page(
                url,
                wait_for=config.content.waitFor,
                permissions=permissions,
            ) as page:
                await extractor.setup_browser(page)
                content = await extractor.extract_content(page, content_config)

        print(f"Scraped content from {url}")
        return ScrapeResult(
            site=site_id,
            operation="content",
            success=True,
            data=content,
        )

    except Exception as e:
        print(f"Error scraping content for {site_id}{path}: {e}")
        return ScrapeResult(
            site=site_id,
            operation="content",
            success=False,
            data=[],
            error=str(e),
        )


# =============================================================================
# Legacy API (backwards compatibility)
# =============================================================================

# Import legacy extractors
from .extract import EXTRACTORS as LEGACY_EXTRACTORS


async def _save_debug_output(page, job: ScrapeJob) -> None:
    """Save debug HTML and screenshot if paths are configured."""
    if job.debug_html_path:
        try:
            html_content = await page.content()
            with open(job.debug_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Debug HTML saved to: {job.debug_html_path}")
        except Exception as html_err:
            print(f"Failed to save debug HTML: {html_err}")

    if job.debug_screenshot_path:
        try:
            await page.screenshot(path=job.debug_screenshot_path, full_page=True)
            print(f"Debug screenshot saved to: {job.debug_screenshot_path}")
        except Exception as ss_err:
            print(f"Failed to save debug screenshot: {ss_err}")


async def scrape(
    job: ScrapeJob,
    parse_fn: ParseFn | None = None,
    extract_fn: ExtractFn | None = None,
) -> LegacyScrapeResult:
    """
    Execute a scrape job (legacy API).

    Args:
        job: Scrape job configuration
        parse_fn: Optional function to parse raw strings into dicts
        extract_fn: Custom extraction function (overrides job.method)
    """
    # Resolve extraction function
    if extract_fn is None:
        if job.method == "custom":
            raise ValueError(f"Job '{job.name}' has method='custom' but no extract_fn provided")
        extract_fn = LEGACY_EXTRACTORS[job.method]

    print(f"Scraping: {job.url}")
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        if job.method == "click_copy":
            permissions = ["clipboard-read", "clipboard-write"]
        else:
            permissions = []
        context = await browser.new_context(permissions=permissions)
        page = await context.new_page()

        try:
            await page.goto(job.url, wait_until=job.wait_until, timeout=job.timeout)

            # Skip wait_for_selector for methods that handle their own waiting
            if job.method not in ("custom", "terraform_registry", "terraform_links"):
                await page.wait_for_selector(job.selector, state="visible", timeout=job.timeout)

            raw_entries = await extract_fn(page, job.selector)

            # Parse if function provided, otherwise keep raw strings
            if parse_fn:
                entries = [parse_fn(r) for r in raw_entries if r]
            else:
                entries = raw_entries

            if len(entries) == 0:
                print(f"No entries found for {job.url}")
                await _save_debug_output(page, job)
                return LegacyScrapeResult(
                    job_name=job.name,
                    url=job.url,
                    success=False,
                    entries=[],
                    error="No entries found",
                )

            print(f"Scraped {len(entries)} entries from {job.url}")
            return LegacyScrapeResult(
                job_name=job.name,
                url=job.url,
                success=True,
                entries=entries,
            )

        except Exception as e:
            print(f"Error scraping {job.url}: {e}")
            await _save_debug_output(page, job)
            return LegacyScrapeResult(
                job_name=job.name,
                url=job.url,
                success=False,
                entries=[],
                error=str(e),
            )


async def scrape_batch(
    jobs: list[ScrapeJob],
    parse_fns: dict[str, ParseFn] | None = None,
    extract_fns: dict[str, ExtractFn] | None = None,
) -> list[LegacyScrapeResult]:
    """
    Execute multiple scrape jobs (legacy API).

    Args:
        jobs: List of scrape jobs
        parse_fns: Dict mapping job name -> parse function
        extract_fns: Dict mapping job name -> extract function
    """
    parse_fns = parse_fns or {}
    extract_fns = extract_fns or {}

    tasks = [
        scrape(
            job,
            parse_fn=parse_fns.get(job.name),
            extract_fn=extract_fns.get(job.name),
        )
        for job in jobs
    ]
    return await asyncio.gather(*tasks)
