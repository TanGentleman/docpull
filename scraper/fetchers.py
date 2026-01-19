"""Fetcher functions for HTTP and browser-based page retrieval."""

import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

import httpx

if TYPE_CHECKING:
    from playwright.async_api import Page, Browser, BrowserContext


async def fetch_html(url: str, timeout: float = 30.0) -> str:
    """
    Fetch HTML content from a URL using httpx.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content as string
    """
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


async def fetch_all_html(urls: list[str], timeout: float = 30.0, concurrency: int = 10) -> dict[str, str]:
    """
    Fetch HTML content from multiple URLs concurrently.

    Args:
        urls: List of URLs to fetch
        timeout: Request timeout in seconds per request
        concurrency: Maximum concurrent requests

    Returns:
        Dict mapping URL to HTML content (or empty string on error)
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, str] = {}

    async def fetch_one(url: str) -> tuple[str, str]:
        async with semaphore:
            try:
                html = await fetch_html(url, timeout)
                return url, html
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return url, ""

    tasks = [fetch_one(url) for url in urls]
    for url, html in await asyncio.gather(*tasks):
        results[url] = html

    return results


@asynccontextmanager
async def browser_context(
    permissions: list[str] | None = None,
) -> AsyncGenerator[tuple["Browser", "BrowserContext"], None]:
    """
    Create a browser context with optional permissions.

    Args:
        permissions: List of browser permissions (e.g., ["clipboard-read", "clipboard-write"])

    Yields:
        Tuple of (browser, context)
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(permissions=permissions or [])
        try:
            yield browser, context
        finally:
            await context.close()
            await browser.close()


@asynccontextmanager
async def browser_page(
    url: str,
    wait_for: str | None = None,
    permissions: list[str] | None = None,
    timeout: int = 30000,
    wait_until: str = "networkidle",
) -> AsyncGenerator["Page", None]:
    """
    Create a browser page, navigate to URL, and optionally wait for a selector.

    Args:
        url: URL to navigate to
        wait_for: Optional CSS selector to wait for
        permissions: List of browser permissions
        timeout: Navigation and wait timeout in milliseconds
        wait_until: Page load event to wait for ("load", "domcontentloaded", "networkidle")

    Yields:
        Playwright Page object
    """
    async with browser_context(permissions=permissions) as (browser, context):
        page = await context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            if wait_for:
                await page.wait_for_selector(wait_for, state="visible", timeout=timeout)
            yield page
        finally:
            await page.close()
