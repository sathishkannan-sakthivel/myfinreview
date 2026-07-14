import json
import os
import logging
import httpx
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class ReferenceDataService:
    _instance = None
    _stocks_cache = {}
    _mf_cache = {}
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReferenceDataService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not ReferenceDataService._initialized:
            self.stocks_cache = ReferenceDataService._stocks_cache
            self.mf_cache = ReferenceDataService._mf_cache
            self._load_stocks()
            self._load_mfs()
            ReferenceDataService._initialized = True
        else:
            # Point instance variables to the class-level caches
            self.stocks_cache = ReferenceDataService._stocks_cache
            self.mf_cache = ReferenceDataService._mf_cache

    def _load_stocks(self):
        # Point directly to backend's own data directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = [
            os.path.join(base_dir, "data", "stocks.json"),
            os.path.join(os.getcwd(), "backend", "data", "stocks.json"),
            "data/stocks.json"
        ]
        logger.debug(f"Searching for stocks.json in {len(paths)} locations...")
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        data = json.load(f)
                        for item in data:
                            self.stocks_cache[item['symbol']] = item['name']
                            # Also cache without suffix for easier matching
                            base_sym = item['symbol'].split('.')[0].upper()
                            if base_sym not in self.stocks_cache:
                                self.stocks_cache[base_sym] = item['name']
                    logger.info(f"Loaded {len(self.stocks_cache)} stocks (including base symbols) from {p}")
                    return
                except Exception as e: 
                    logger.error(f"Failed to load stocks from {p}: {e}")
        logger.warning(f"No stocks.json found. Current Working Directory: {os.getcwd()}")

    def _load_mfs(self):
        # Point directly to backend's own data directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = [
            os.path.join(base_dir, "data", "mutualfunds.json"),
            os.path.join(os.getcwd(), "backend", "data", "mutualfunds.json"),
            "data/mutualfunds.json"
        ]
        logger.debug(f"Searching for mutualfunds.json in {len(paths)} locations...")
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                self.mf_cache[str(item.get('symbol', ''))] = item
                        else:
                            self.mf_cache = data
                    logger.info(f"Loaded {len(self.mf_cache)} mutual funds from {p}")
                    return
                except Exception as e:
                    logger.error(f"Failed to load mutual funds from {p}: {e}")
        logger.warning(f"No mutualfunds.json found. Current Working Directory: {os.getcwd()}")

    def get_all_stocks(self):
        """Returns the full stocks database in list format for the frontend."""
        # Convert dictionary back to the list format the frontend expects
        # We only return items that have a .NS suffix to avoid duplicates in the frontend list
        return [{"symbol": s, "name": n} for s, n in self.stocks_cache.items() if s.endswith('.NS')]

    def get_all_mfs(self):
        """Returns the full mutual funds database."""
        return self.mf_cache

    def get_asset_name(self, symbol: str) -> Optional[str]:
        if not symbol: return None
        s = str(symbol).strip().upper()
        
        # 1. Direct match
        if s in self.stocks_cache:
            logger.debug(f"Found {s} in stocks_cache")
            return self.stocks_cache[s]
        
        # 2. Base symbol match (remove .NS, .BO)
        base = s.split('.')[0]
        if base in self.stocks_cache:
            logger.debug(f"Found base {base} in stocks_cache")
            return self.stocks_cache[base]

        # 3. Mutual Fund match
        if s in self.mf_cache:
            logger.debug(f"Found {s} in mf_cache")
            mf_item = self.mf_cache[s]
            return mf_item.get('name') if isinstance(mf_item, dict) else str(mf_item)
        
        if s.isdigit():
            logger.debug(f"{s} looks like MF ID, attempting API fallback...")
            # choose sync or async fetch depending on event loop state
            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    # inside async context, use sync httpx client to avoid re-entering loop
                    return self._fetch_mf_name_api_sync(s)
                else:
                    return asyncio.run(self._fetch_mf_name_api(s))
            except Exception:
                return None
        
        logger.debug(f"No name found for symbol: {s}")
        return None

    async def _fetch_mf_name_api(self, symbol: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                res = await client.get(f"https://api.mfapi.in/mf/{symbol}")
                if res.status_code == 200:
                    return res.json().get('meta', {}).get('scheme_name')
        except Exception as e:
            logger.warning(f"MF name API lookup failed for {symbol}: {e}")
        return None

    def _fetch_mf_name_api_sync(self, symbol: str) -> Optional[str]:
        """Synchronous fallback when running inside an event loop."""
        try:
            with httpx.Client(timeout=5) as client:
                res = client.get(f"https://api.mfapi.in/mf/{symbol}")
                if res.status_code == 200:
                    return res.json().get('meta', {}).get('scheme_name')
        except Exception as e:
            logger.warning(f"Sync MF name API lookup failed for {symbol}: {e}")
        return None
