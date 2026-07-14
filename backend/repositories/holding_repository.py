from .dynamo_client import DynamoClient

class HoldingRepository:
    def __init__(self):
        self.client = DynamoClient()

    def get_user_holdings(self, user_id):
        return self.client.query_items(f'USER#{user_id}', 'HOLDING#')

    def save_holding(self, user_id, symbol, holding_data):
        item = {
            'PK': f'USER#{user_id}',
            'SK': f'HOLDING#{symbol}',
            **holding_data
        }
        return self.client.put_item(item)

    def get_holding(self, user_id, symbol):
        return self.client.get_item(f'USER#{user_id}', f'HOLDING#{symbol}')
