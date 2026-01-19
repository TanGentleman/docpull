"""Cursor docs extractor using click_copy pattern."""

from typing import TYPE_CHECKING

from .default import DefaultExtractor
from . import register

if TYPE_CHECKING:
    from playwright.async_api import Page


@register("cursor")
class CursorExtractor(DefaultExtractor):
    """Extractor for Cursor documentation.

    Uses:
    - HTTP fetch for link discovery
    - Browser with click_copy for content extraction
    """

    async def extract_content(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract content using Cursor's copy page button."""
        if isinstance(page_or_html, str):
            # Fetch mode: return HTML as-is
            return [page_or_html]

        page = page_or_html
        selector = config.get(
            "selector",
            '//button[@type="button"][.//span[text()="Copy page"]]'
        )

        # Wait for the copy button to be visible
        await page.wait_for_selector(selector, state="visible", timeout=30000)

        return await self._click_copy(page, selector)
