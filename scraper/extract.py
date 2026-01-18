"""Extraction strategies for scraping."""

from playwright.async_api import Page


async def terraform_registry(page: Page, selector: str) -> list[str]:
    """Custom extraction for Terraform Registry - handles cookie consent and JS rendering."""
    # Handle cookie consent banner if present
    try:
        accept_button = page.locator('button:has-text("Accept All")')
        await accept_button.wait_for(state="visible", timeout=5000)
        await accept_button.click()
        await page.wait_for_timeout(1000)
    except Exception:
        pass  # No cookie banner or already dismissed

    # Wait for the actual content to render (JS-heavy SPA)
    await page.wait_for_selector(selector, state="visible", timeout=30000)
    await page.wait_for_timeout(1000)  # Extra time for JS to settle

    # Extract innerHTML
    elements = await page.query_selector_all(selector)
    results = []
    for el in elements:
        html = await el.inner_html()
        results.append(html.strip() if html else "")
    return results


async def click_copy(page: Page, selector: str) -> list[str]:
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


async def text_content(page: Page, selector: str) -> list[str]:
    """Extract textContent from all matching elements. Supports CSS and XPath."""
    elements = await page.query_selector_all(selector)
    results = []
    for el in elements:
        text = await el.text_content()
        results.append(text.strip() if text else "")
    return results


async def inner_html(page: Page, selector: str) -> list[str]:
    """Extract innerHTML from all matching elements. Supports CSS and XPath."""
    elements = await page.query_selector_all(selector)
    results = []
    for el in elements:
        html = await el.inner_html()
        results.append(html.strip() if html else "")
    return results


# Registry for string-based lookup
EXTRACTORS = {
    "click_copy": click_copy,
    "text_content": text_content,
    "inner_html": inner_html,
    "terraform_registry": terraform_registry,
}
