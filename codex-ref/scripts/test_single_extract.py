#!/usr/bin/env python3
"""Test LLM extraction on a single known URL to verify the pipeline works.
Run: python scripts/test_single_extract.py [url]

Default URL: https://acquire.com/marketplace (safe, public, no bot protection)
"""

import asyncio
import json
import os
import sys

DEFAULT_URL = "https://acquire.com/marketplace"


async def test_extract(url: str):
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("FAIL: Need DEEPSEEK_API_KEY or OPENAI_API_KEY in .env")
        sys.exit(1)

    provider = (
        "deepseek/deepseek-chat" if os.getenv("DEEPSEEK_API_KEY") else "openai/gpt-4o"
    )

    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=50,
        bypass_cache=True,
    )

    print(f"Crawling: {url}")
    print(f"Provider: {provider}")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

        if not result.success:
            print(f"FAIL: Crawl failed — {result.error_message}")
            sys.exit(1)

        word_count = len(result.markdown.split()) if result.markdown else 0
        link_count = len(result.links.get("internal", [])) if result.links else 0

        print(f"\n  OK: Crawl succeeded")
        print(f"  Words: {word_count}")
        print(f"  Internal links: {link_count}")
        print(
            f"  Title: {result.metadata.get('title', 'N/A') if result.metadata else 'N/A'}"
        )

        if word_count < 50:
            print(f"\n  WARNING: Only {word_count} words — possible bot block page")

        # Show first 500 chars of markdown
        if result.markdown:
            preview = result.markdown[:500].replace("\n", " ")
            print(f"\n  Preview: {preview}...")

        print(f"\n  Links discovered: {link_count}")
        if result.links and result.links.get("internal"):
            for link in result.links["internal"][:10]:
                href = link.get("href", link) if isinstance(link, dict) else link
                print(f"    → {href}")

    print("\nPASS: Basic crawl working")


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    asyncio.run(test_extract(url))


if __name__ == "__main__":
    main()
