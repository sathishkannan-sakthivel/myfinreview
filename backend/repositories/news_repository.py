from .dynamo_client import DynamoClient
from datetime import datetime
import uuid

class NewsRepository:
    def __init__(self):
        self.client = DynamoClient()

    def save_news_item(self, symbol, title, url, sentiment="NEUTRAL"):
        timestamp = datetime.utcnow().isoformat()
        item = {
            'PK': f'NEWS#{symbol}',
            'SK': f'TS#{timestamp}',
            'symbol': symbol,
            'title': title,
            'url': url,
            'sentiment': sentiment,
            'timestamp': timestamp,
            'id': str(uuid.uuid4())
        }
        return self.client.put_item(item)

    def get_news_for_symbol(self, symbol, limit=10):
        # Queries for PK=NEWS#<symbol>, SK starts_with(TS#)
        # Using query_items from DynamoClient
        return self.client.query_items(f'NEWS#{symbol}', 'TS#')[:limit]

    def get_latest_news_for_user(self, symbols, limit_per_symbol=5):
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_news_for_symbol(symbol, limit=limit_per_symbol)
        return results
