import asyncio
import logging
import httpx
from .base_provider import BaseProvider
from config import settings

logger = logging.getLogger(__name__)

class YahooFinanceProvider(BaseProvider):
    """
    Async implementation using Yahoo Finance via httpx.
    """
    def __init__(self, timeout=None, retries=None):
        self.timeout = timeout or settings.PROVIDER_TIMEOUT
        self.retries = retries or settings.PROVIDER_RETRIES
        self.base_url = settings.MARKET_DATA_BASE_URL
        self.headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        # track symbols that definitively do not exist (e.g. ^NSENI)
        self._not_found = set()

    async def get_price(self, symbol: str) -> float:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._fetch_single_price(symbol, client)

    async def get_batch_prices(self, symbols: list) -> dict:
        results = {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Parallelize fetching all symbols at once
            tasks = [self._fetch_single_price(symbol, client) for symbol in symbols]
            prices = await asyncio.gather(*tasks)
            for symbol, price in zip(symbols, prices):
                if price:
                    results[symbol] = price
        return results

    async def _fetch_single_price(self, symbol: str, client: httpx.AsyncClient) -> dict:
        # short‑circuit if we already know the symbol is invalid
        if symbol in self._not_found:
            return None

        attempt = 0
        while attempt < self.retries:
            try:
                url = f"{self.base_url}{symbol}"
                resp = await client.get(url, headers=self.headers)
                # 404 means ticker isn't recognised; record and bail out immediately
                if resp.status_code == 404:
                    logger.warning(f"Yahoo symbol not found: {symbol} (404)")
                    self._not_found.add(symbol)
                    return None
                resp.raise_for_status()
                data = resp.json()
                
                # Extract meta info
                meta = data['chart']['result'][0]['meta']
                price = meta.get('regularMarketPrice')
                prev_close = meta.get('chartPreviousClose') # For change % calculation
                # If shortName is available, use it for metadata enrichment
                name = meta.get('shortName', meta.get('symbol'))
                
                return {"price": float(price), "name": name, "prev_close": prev_close}
            except httpx.HTTPStatusError as e:
                # handle other HTTP errors
                attempt += 1
                logger.warning(f"Yahoo fetch status error for {symbol} attempt {attempt}: {e}")
            except Exception as e:
                attempt += 1
                logger.warning(f"Yahoo fetch error for {symbol} attempt {attempt}: {e}")

            if attempt >= self.retries:
                return None
            await asyncio.sleep(1)
        return None
