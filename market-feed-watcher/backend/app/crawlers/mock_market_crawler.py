import asyncio
from bs4 import BeautifulSoup

from app.crawlers.mock_market_pages import (
    MOCK_MARKET_HTML_BATCH_1,
    MOCK_MARKET_HTML_BATCH_2,
)

class MockMarketCrawler:
    def __init__(self):
        self.run_count = 0

    async def fetch_html(self) -> str:
        """
        Simulates fetching HTML from an external marketplace.

        Real version could use:
        - httpx.AsyncClient
        - retries
        - timeout handling
        - proxy rotation
        - user-agent headers
        """

        await asyncio.sleep(1)

        self.run_count += 1

        if self.run_count == 1:
            return MOCK_MARKET_HTML_BATCH_1

        return MOCK_MARKET_HTML_BATCH_2

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