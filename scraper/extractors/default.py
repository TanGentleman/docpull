"""Default extractors for generic link and content extraction."""

import re
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from . import Extractor, register

if TYPE_CHECKING:
    from playwright.async_api import Page


@register("default")
class DefaultExtractor(Extractor):
    """Generic extractor for standard documentation sites."""

    async def extract_links(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract links from HTML using regex (fetch mode) or page evaluation (browser mode)."""
        base_url = config.get("baseUrl", "")
        pattern = config.get("pattern", "")

        if isinstance(page_or_html, str):
            # Fetch mode: parse HTML string
            return self._extract_links_from_html(page_or_html, base_url, pattern)
        else:
            # Browser mode: evaluate on page
            return await self._extract_links_from_page(page_or_html, base_url, pattern)

    async def extract_content(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract content based on method specified in config."""
        method = config.get("method", "inner_html")
        selector = config.get("selector", "body")

        if isinstance(page_or_html, str):
            # Fetch mode: return the HTML as-is (or could parse)
            return [page_or_html]

        # Browser mode
        page = page_or_html

        if method == "click_copy":
            return await self._click_copy(page, selector)
        elif method == "text_content":
            return await self._text_content(page, selector)
        else:  # inner_html
            return await self._inner_html(page, selector)

    def _extract_links_from_html(self, html: str, base_url: str, pattern: str) -> list[str]:
        """Extract links from HTML string using regex."""
        links = set()
        for match in re.finditer(r'href="([^"]*)"', html):
            link = match.group(1)
            link = self._clean_url(link)

            # Resolve relative URLs
            if link.startswith("/"):
                parsed = urlparse(base_url)
                link = f"{parsed.scheme}://{parsed.netloc}{link}"
            elif not link.startswith("http"):
                link = urljoin(base_url, link)

            # Filter by pattern
            if pattern and pattern not in link:
                continue

            # Only include links from same domain
            if urlparse(link).netloc == urlparse(base_url).netloc:
                links.add(link)

        return sorted(links)

    async def _extract_links_from_page(self, page: "Page", base_url: str, pattern: str) -> list[str]:
        """Extract links from a Playwright page."""
        raw_links = await page.eval_on_selector_all(
            "a[href]",
            "elements => elements.map(e => e.href)"
        )

        links = set()
        for link in raw_links:
            link = self._clean_url(link)
            if pattern and pattern not in link:
                continue
            if link.startswith(base_url) or urlparse(link).netloc == urlparse(base_url).netloc:
                links.add(link)

        return sorted(links)

    async def _click_copy(self, page: "Page", selector: str) -> list[str]:
        """Click a copy button and read clipboard content."""
        await page.click(selector)
        await page.wait_for_timeout(1000)

        content = await page.evaluate("""
            async () => {
                try {
                    return await navigator.clipboard.readText();
                } catch (err) {
                    return `Error reading clipboard: ${err.message}`;
                }
            }
        """)
        return [content] if content else []

    async def _text_content(self, page: "Page", selector: str) -> list[str]:
        """Extract text content from all matching elements."""
        elements = await page.query_selector_all(selector)
        results = []
        for el in elements:
            text = await el.text_content()
            results.append(text.strip() if text else "")
        return results

    async def _inner_html(self, page: "Page", selector: str) -> list[str]:
        """Extract innerHTML from all matching elements."""
        elements = await page.query_selector_all(selector)
        results = []
        for el in elements:
            html = await el.inner_html()
            results.append(html.strip() if html else "")
        return results
