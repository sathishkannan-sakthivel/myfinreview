from .dynamo_client import DynamoClient
from datetime import datetime
import uuid

class TransactionRepository:
    def __init__(self):
        self.client = DynamoClient()

    def record_transaction(self, user_id, symbol, tx_data):
        timestamp = tx_data.get('timestamp', datetime.utcnow().isoformat())
        tx_id = str(uuid.uuid4())
        item = {
            'PK': f'USER#{user_id}',
            'SK': f'TX#{symbol}#{timestamp}#{tx_id}',
            'TX_ID': tx_id,
            'SYMBOL': symbol,
            **tx_data
        }
        return self.client.put_item(item)

    def get_transactions(self, user_id, symbol=None):
        sk_prefix = f'TX#{symbol}' if symbol else 'TX#'
        return self.client.query_items(f'USER#{user_id}', sk_prefix)
