"""Terraform Registry extractor for JS-heavy SPA."""

from typing import TYPE_CHECKING

from . import Extractor, register

if TYPE_CHECKING:
    from playwright.async_api import Page


@register("terraform")
class TerraformExtractor(Extractor):
    """Extractor for Terraform Registry (JS-heavy SPA).

    Handles:
    - Cookie consent banner dismissal
    - Waiting for SPA content to render
    - Link extraction from sidebar navigation
    """

    async def setup_browser(self, page: "Page") -> None:
        """Handle cookie consent banner."""
        try:
            btn = page.locator('button:has-text("Accept All")')
            await btn.wait_for(state="visible", timeout=5000)
            await btn.click()
            await page.wait_for_timeout(1000)
        except Exception:
            pass  # No cookie banner or already dismissed

    async def extract_links(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract all doc links from Terraform Registry.

        Note: This extractor only supports browser mode due to the JS-heavy SPA nature.
        """
        if isinstance(page_or_html, str):
            raise ValueError("TerraformExtractor requires browser mode for link extraction")

        page = page_or_html
        base_url = config.get("baseUrl", "")
        wait_for = config.get("waitFor", "#provider-docs-content")

        # Handle cookie consent
        await self.setup_browser(page)

        # Wait for content to render
        await page.wait_for_selector(wait_for, state="visible", timeout=30000)
        await page.wait_for_timeout(2000)  # Extra time for JS to settle

        # Extract all links
        links = await page.eval_on_selector_all(
            "a[href]",
            "elements => elements.map(e => e.href)"
        )

        # Filter to docs links only
        results = set()
        for link in links:
            clean_link = self._clean_url(link)
            if clean_link.startswith(base_url):
                results.add(clean_link)

        return sorted(results)

    async def extract_content(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract documentation content from Terraform Registry.

        Note: This extractor only supports browser mode.
        """
        if isinstance(page_or_html, str):
            raise ValueError("TerraformExtractor requires browser mode for content extraction")

        page = page_or_html
        selector = config.get("selector", "#provider-docs-content")

        # Handle cookie consent
        await self.setup_browser(page)

        # Wait for content to render
        await page.wait_for_selector(selector, state="visible", timeout=30000)
        await page.wait_for_timeout(1000)

        # Extract innerHTML
        elements = await page.query_selector_all(selector)
        results = []
        for el in elements:
            html = await el.inner_html()
            results.append(html.strip() if html else "")
        return results
