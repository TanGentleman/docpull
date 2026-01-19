"""CLI for the scraper package.

Usage:
    python -m scraper sites                              # List all available sites
    python -m scraper links modal                        # Get all doc links for Modal
    python -m scraper content terraform-aws /resources/aws_instance
    python -m scraper info modal                         # Show site configuration
"""

import argparse
import asyncio
import json
import sys

from .core import scrape_links, scrape_content, list_sites, load_site_config


def _print_result(result, json_mode: bool, content_mode: bool) -> int:
    if json_mode:
        print(json.dumps(result.model_dump(), indent=2))
        return 0 if result.success else 1

    if not result.success:
        print(result.error or "Unknown error", file=sys.stderr)
        return 1

    if content_mode:
        print("\n".join(result.data))
    else:
        for link in result.data:
            print(link)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scraper CLI for documentation sites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_sites = subparsers.add_parser("sites", help="List available site IDs")
    parser_sites.add_argument("--json", action="store_true", help="Output JSON")

    parser_links = subparsers.add_parser("links", help="Scrape links for a site")
    parser_links.add_argument("site_id", help="Site identifier (e.g., modal)")
    parser_links.add_argument("--json", action="store_true", help="Output JSON")

    parser_content = subparsers.add_parser("content", help="Scrape content for a page")
    parser_content.add_argument("site_id", help="Site identifier (e.g., terraform-aws)")
    parser_content.add_argument("path", nargs="?", default="", help="Path relative to baseUrl")
    parser_content.add_argument("--json", action="store_true", help="Output JSON")

    parser_info = subparsers.add_parser("info", help="Show site configuration")
    parser_info.add_argument("site_id", help="Site identifier")

    args = parser.parse_args()

    if args.command == "sites":
        sites = list_sites()
        if args.json:
            print(json.dumps({"sites": sites, "count": len(sites)}, indent=2))
        else:
            for site in sites:
                print(site)
        return 0

    if args.command == "links":
        result = asyncio.run(scrape_links(args.site_id))
        return _print_result(result, args.json, content_mode=False)

    if args.command == "content":
        result = asyncio.run(scrape_content(args.site_id, args.path))
        return _print_result(result, args.json, content_mode=True)

    if args.command == "info":
        try:
            config = load_site_config(args.site_id)
            print(f"Site: {config.name}")
            print(f"Base URL: {config.baseUrl}")
            print(f"Mode: {config.mode}")
            print(f"Extractor: {config.extractor}")
            if config.links:
                print(f"Links config:")
                print(f"  Start URLs: {config.links.startUrls}")
                print(f"  Pattern: {config.links.pattern}")
                print(f"  Max depth: {config.links.maxDepth}")
            if config.content:
                print(f"Content config:")
                print(f"  Method: {config.content.method}")
                print(f"  Selector: {config.content.selector}")
            return 0
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())



