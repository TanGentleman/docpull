"""Extractor base class and registry."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

# Registry for string-based lookup
EXTRACTORS: dict[str, type["Extractor"]] = {}


def register(name: str):
    """Decorator to register an extractor."""
    def wrapper(cls: type["Extractor"]) -> type["Extractor"]:
        EXTRACTORS[name] = cls
        return cls
    return wrapper


def get_extractor(name: str) -> "Extractor":
    """Get an extractor instance by name."""
    if name not in EXTRACTORS:
        raise ValueError(f"Unknown extractor: {name}. Available: {list(EXTRACTORS.keys())}")
    return EXTRACTORS[name]()


class Extractor(ABC):
    """Base class for site-specific extractors."""

    async def setup_browser(self, page: "Page") -> None:
        """Optional: Handle cookie consent, login, etc."""
        pass

    @abstractmethod
    async def extract_links(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract all documentation links.

        Args:
            page_or_html: Either a Playwright Page (browser mode) or HTML string (fetch mode)
            config: The site's links configuration dict

        Returns:
            List of discovered URLs
        """
        pass

    @abstractmethod
    async def extract_content(self, page_or_html: "Page | str", config: dict) -> list[str]:
        """Extract page content.

        Args:
            page_or_html: Either a Playwright Page (browser mode) or HTML string (fetch mode)
            config: The site's content configuration dict

        Returns:
            List of content strings (HTML or text)
        """
        pass

    def _clean_url(self, url: str) -> str:
        """Remove query params and fragments from URL."""
        return url.split("?")[0].split("#")[0].rstrip("/")


# Import extractors to trigger registration
from . import default
from . import terraform
from . import modal
from . import convex
from . import cursor
from . import claude_code
from . import unsloth

__all__ = ["Extractor", "EXTRACTORS", "register", "get_extractor"]
