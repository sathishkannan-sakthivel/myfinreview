import asyncio
import logging
import httpx
from .base_provider import BaseProvider
from config import settings

logger = logging.getLogger(__name__)

class MFAPIProvider(BaseProvider):
    """
    Async implementation using mfapi.in for Indian Mutual Fund NAVs.
    """
    def __init__(self, timeout=None, retries=None):
        self.timeout = timeout or settings.PROVIDER_TIMEOUT
        self.retries = retries or settings.PROVIDER_RETRIES
        self.base_url = settings.MFAPI_BASE_URL

    async def get_price(self, symbol: str) -> float:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._fetch_single_price(symbol, client)

    async def _fetch_single_price(self, symbol: str, client: httpx.AsyncClient) -> dict:
        attempt = 0
        while attempt < self.retries:
            try:
                url = f"{self.base_url}{symbol}"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if data and 'data' in data and len(data['data']) > 0:
                    latest_nav = data['data'][0]['nav']
                    scheme_name = data.get('meta', {}).get('scheme_name')
                    return {"price": float(latest_nav), "name": scheme_name}
                return None
            except Exception as e:
                logger.warning(f"Error fetching NAV for {symbol}: {e}")
                attempt += 1
                if attempt == self.retries:
                    return None
                await asyncio.sleep(1)
        return None

    async def get_batch_prices(self, symbols: list) -> dict:
        results = {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [self._fetch_single_price(symbol, client) for symbol in symbols]
            fetched_data = await asyncio.gather(*tasks)
            for symbol, data in zip(symbols, fetched_data):
                if data:
                    # Return the full data object so the service can use the name
                    results[symbol] = data
        return results

    async def get_historical_data(self, symbol: str) -> list:
        try:
            url = f"{self.base_url}{symbol}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return data.get('data', [])
        except Exception as e:
            logger.error(f"Error fetching historical NAV for {symbol}: {e}")
            return []
