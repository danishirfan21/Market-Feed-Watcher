import asyncio
import httpx
from bs4 import BeautifulSoup

class HttpMarketCrawler:
    def __init__(
        self,
        source: str,
        url: str,
        timeout_seconds: float = 5.0,
        max_retries: int = 3,
    ):
        self.source = source
        self.url = url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def fetch_html_once(self) -> str:
        headers = {
            "User-Agent": (
                "MarketFeedWatcher/0.1 "
                "(educational crawler demo; contact: local-demo)"
            )
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.url, headers=headers)
            response.raise_for_status()
            return response.text

    async def fetch_html(self) -> str:
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return await self.fetch_html_once()
            except Exception as exc:
                last_error = exc

                if attempt < self.max_retries:
                    await asyncio.sleep(attempt * 0.5)

        raise RuntimeError(
            f"Failed to fetch {self.url} after {self.max_retries} attempts: {last_error}"
        )

    def parse_listings(self, html: str) -> list[dict]:
        """
        Generic parser placeholder.

        This expects HTML shaped like:

        <div class="listing" data-id="car-001">
          <h2>2019 Honda Civic</h2>
          <span class="price">5200000</span>
          <span class="status">available</span>
        </div>

        In production, each source would usually need its own parser.
        """

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
                    "source": self.source,
                }
            )

        return listings

    async def fetch_listings(self) -> list[dict]:
        html = await self.fetch_html()
        return self.parse_listings(html)