"""Convex docs extractor using click_copy pattern."""

from typing import TYPE_CHECKING

from .default import DefaultExtractor
from . import register

if TYPE_CHECKING:
    from playwright.async_api import Page


@register("convex")
class ConvexExtractor(DefaultExtractor):
    """Extractor for Convex documentation.

    Uses:
    - HTTP fetch for link discovery (Docusaurus-based static HTML)
    - Browser with click_copy for content extraction
    """

    async def extract_content(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract content using Convex's copy page button."""
        if isinstance(page_or_html, str):
            # Fetch mode: return HTML as-is
            return [page_or_html]

        page = page_or_html
        selector = config.get(
            "selector",
            '//*[@id="__docusaurus_skipToContent_fallback"]/div/div/main/div/div/div[1]/div/article/div[1]/button'
        )

        # Wait for the copy button to be visible
        await page.wait_for_selector(selector, state="visible", timeout=30000)

        return await self._click_copy(page, selector)
