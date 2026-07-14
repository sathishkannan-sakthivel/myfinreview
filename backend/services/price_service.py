from repositories.dynamo_client import DynamoClient
from providers.yahoo_finance_provider import YahooFinanceProvider
from providers.mfapi_provider import MFAPIProvider
from datetime import datetime, timedelta
from config import settings

class PriceService:
    def __init__(self):
        self.client = DynamoClient()
        self.stock_provider = YahooFinanceProvider(
            timeout=settings.PROVIDER_TIMEOUT,
            retries=settings.PROVIDER_RETRIES
        )
        self.mf_provider = MFAPIProvider(
            timeout=settings.PROVIDER_TIMEOUT,
            retries=settings.PROVIDER_RETRIES
        )
        self.cache_duration_minutes = settings.PRICE_CACHE_MINUTES

    def _get_provider_for_symbol(self, symbol: str):
        """
        Logic to determine which provider to use:
        - Numeric symbols are treated as MF scheme codes (mfapi.in)
        - Alphanumeric symbols are treated as Stock tickers (Yahoo Finance)
        """
        if str(symbol).isdigit():
            return self.mf_provider
        return self.stock_provider

    def get_latest_price(self, symbol):
        # 1. Check DynamoDB Cache first
        price_item = self.client.get_item(f'PRICE#{symbol}', 'LATEST')
        
        if price_item:
            timestamp_str = price_item.get('timestamp')
            timestamp = datetime.fromisoformat(timestamp_str)
            if datetime.utcnow() - timestamp < timedelta(minutes=self.cache_duration_minutes):
                print(f"Cache hit for {symbol}")
                return price_item.get('price')

        # 2. Cache miss or expired -> Fetch from Provider
        print(f"Cache miss/expired for {symbol}. Fetching from provider...")
        provider = self._get_provider_for_symbol(symbol)
        price = provider.get_price(symbol)
        
        if price:
            self.save_price(symbol, price)
            return price
        
        # 3. Fallback to stale cache if provider fails
        return price_item.get('price') if price_item else None

    def save_price(self, symbol, price):
        timestamp = datetime.utcnow().isoformat()
        item = {
            'PK': f'PRICE#{symbol}',
            'SK': 'LATEST',
            'price': float(price),
            'timestamp': timestamp
        }
        self.client.put_item(item)
        
        # Store in history
        hist_item = {
            'PK': f'PRICE#{symbol}',
            'SK': f'HIST#{timestamp}',
            'price': float(price),
            'timestamp': timestamp
        }
        self.client.put_item(hist_item)

    def refresh_prices(self, symbols):
        if not symbols:
            return True
            
        # Group symbols by provider
        stock_symbols = [s for s in symbols if not str(s).isdigit()]
        mf_symbols = [s for s in symbols if str(s).isdigit()]

        results = {}
        if stock_symbols:
            results.update(self.stock_provider.get_batch_prices(stock_symbols))
        if mf_symbols:
            results.update(self.mf_provider.get_batch_prices(mf_symbols))

        for symbol, price in results.items():
            if price:
                self.save_price(symbol, price)
        return True
