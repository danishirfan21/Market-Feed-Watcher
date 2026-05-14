import asyncio
from app.seed_data import MOCK_LISTINGS_BATCH_1, MOCK_LISTINGS_BATCH_2

class MockMarketCrawler:
    def __init__(self):
        self.run_count = 0

    async def fetch_listings(self):
        """
        Simulates an async crawler fetching marketplace listings.

        In a real crawler, this is where we would:
        - call external pages/APIs
        - use httpx/aiohttp
        - parse HTML/JSON
        - normalize listing records
        - handle retries/timeouts
        """

        await asyncio.sleep(1)

        self.run_count += 1

        if self.run_count == 1:
            return MOCK_LISTINGS_BATCH_1

        return MOCK_LISTINGS_BATCH_2