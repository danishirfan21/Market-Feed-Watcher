import asyncio
import random
from bs4 import BeautifulSoup

from app.crawlers.mock_market_pages import (
    MOCK_MARKET_HTML_BATCH_1,
    MOCK_MARKET_HTML_BATCH_2,
)

class MockMarketCrawler:
    def __init__(self):
        self.run_count = 0
        self.max_retries = 3
        self.timeout_seconds = 2

    async def fetch_html_once(self) -> str:
        """
        Simulates a single external marketplace fetch.

        Real version could use:
        - httpx.AsyncClient
        - timeout handling
        - retry/backoff
        - proxy rotation
        - source-specific headers
        """

        await asyncio.sleep(0.6)

        self.run_count += 1

        should_fail = random.random() < 0.25

        if should_fail:
            raise TimeoutError("Simulated upstream timeout while fetching market page")

        if self.run_count == 1:
            return MOCK_MARKET_HTML_BATCH_1

        return MOCK_MARKET_HTML_BATCH_2

    async def fetch_html(self) -> str:
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return await asyncio.wait_for(
                    self.fetch_html_once(),
                    timeout=self.timeout_seconds,
                )
            except Exception as exc:
                last_error = exc

                if attempt < self.max_retries:
                    await asyncio.sleep(attempt * 0.5)

        raise RuntimeError(
            f"Failed to fetch market page after {self.max_retries} attempts: {last_error}"
        )

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        listing_nodes = soup.select(".listing")

        listings = []

        for node in listing_nodes:
            external_id = node.get("data-id")
            title_node = node.select_one("h2")
            price_node = node.select_one(".price")
            status_node = node.select_one(".status")

            if not external_id or not title_node or not price_node or not status_node:
                continue

            listings.append(
                {
                    "external_id": external_id.strip(),
                    "title": title_node.text.strip(),
                    "price": int(price_node.text.strip()),
                    "status": status_node.text.strip(),
                    "source": "mock_html_market",
                }
            )

        return listings

    async def fetch_listings(self) -> list[dict]:
        html = await self.fetch_html()
        return self.parse_listings(html)