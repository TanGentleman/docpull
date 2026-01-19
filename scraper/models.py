"""Type definitions for scrape jobs and results."""

from typing import Callable, Awaitable, Literal
from pydantic import BaseModel
from playwright.async_api import Page

# Type aliases
Mode = Literal["fetch", "browser"]
Operation = Literal["links", "content"]
ExtractMethod = Literal["click_copy", "text_content", "inner_html", "custom"]
ExtractFn = Callable[[Page, str], Awaitable[list[str]]]
ParseFn = Callable[[str], dict]


class LinksConfig(BaseModel):
    """Configuration for link discovery."""
    startUrls: list[str] = [""]
    pattern: str = ""
    waitFor: str | None = None
    maxDepth: int = 2


class ContentConfig(BaseModel):
    """Configuration for content extraction."""
    mode: Mode | None = None  # Override site mode for content
    waitFor: str | None = None
    selector: str = "body"
    method: ExtractMethod = "inner_html"


class SiteConfig(BaseModel):
    """Site configuration loaded from JSON."""
    name: str
    baseUrl: str
    mode: Mode
    extractor: str
    links: LinksConfig | None = None
    content: ContentConfig | None = None


class ScrapeResult(BaseModel):
    """Result from any scrape operation."""
    site: str
    operation: Operation
    success: bool
    data: list[str]
    error: str | None = None


# Legacy types for backwards compatibility
class ScrapeJob(BaseModel):
    """Configuration for a scrape job (legacy)."""
    name: str
    url: str
    selector: str
    method: ExtractMethod | Literal["terraform_registry", "terraform_links"] = "text_content"
    timeout: int = 30000
    wait_until: Literal["load", "domcontentloaded", "networkidle"] = "networkidle"
    debug_html_path: str | None = None
    debug_screenshot_path: str | None = None

    class Config:
        extra = "allow"


class LegacyScrapeResult(BaseModel):
    """Result from a scrape job (legacy)."""
    job_name: str
    url: str
    success: bool
    entries: list[dict | str]
    error: str | None = None
