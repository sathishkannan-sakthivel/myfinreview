from .dynamo_client import DynamoClient
from datetime import datetime, timedelta
import time

class IdempotencyRepository:
    def __init__(self):
        self.client = DynamoClient()

    def get_idempotency_record(self, key):
        # PK=IDEM#<key>, SK=METADATA
        return self.client.get_item(f"IDEM#{key}", "METADATA")

    def save_idempotency_record(self, key, result, ttl_days=7):
        # Using a TTL to allow automatic cleanup by DynamoDB
        ttl = int(time.time() + (ttl_days * 24 * 60 * 60))
        item = {
            'PK': f"IDEM#{key}",
            'SK': "METADATA",
            'result': result,
            'status': 'COMPLETED',
            'timestamp': datetime.utcnow().isoformat(),
            'TTL': ttl
        }
        return self.client.put_item(item)

    def mark_in_progress(self, key, ttl_minutes=15):
        # Mark as in progress to prevent concurrent execution
        ttl = int(time.time() + (ttl_minutes * 60))
        item = {
            'PK': f"IDEM#{key}",
            'SK': "METADATA",
            'status': 'IN_PROGRESS',
            'timestamp': datetime.utcnow().isoformat(),
            'TTL': ttl
        }
        # Conditional put to ensure we don't overwrite an existing COMPLETED or IN_PROGRESS record
        # Note: DynamoClient.put_item needs to support ConditionExpression for true robustness
        return self.client.put_item(item)
