from .dynamo_client import DynamoClient
from datetime import datetime

class InsightsRepository:
    def __init__(self):
        self.client = DynamoClient()

    def save_insight(self, user_id, content, type="SUMMARY", **kwargs):
        timestamp = datetime.utcnow().isoformat()
        item = {
            'PK': f'USER#{user_id}',
            'SK': f'INSIGHT#{type}#{timestamp}',
            'content': content,
            'type': str(type),
            'timestamp': timestamp,
            **kwargs
        }
        self.client.put_item(item)
        
        # Also save as LATEST
        latest_item = item.copy()
        latest_item['SK'] = f'INSIGHT#{type}#LATEST'
        return self.client.put_item(latest_item)

    def get_latest_insight(self, user_id, type="SUMMARY"):
        return self.client.get_item(f'USER#{user_id}', f'INSIGHT#{type}#LATEST')
    
    def get_insights_history(self, user_id, type="SUMMARY", limit=10):
        return self.client.query_items(f'USER#{user_id}', f'INSIGHT#{type}#')[:limit]
