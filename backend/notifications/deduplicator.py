from typing import Dict, Any, List
from datetime import datetime, timedelta
from repositories.dynamo_client import DynamoClient

class NotificationDeduplicator:
    """
    Prevents duplicate notifications for the same event type within a time window.
    """
    def __init__(self, window_hours: int = 4):
        self.window_hours = window_hours
        self.client = DynamoClient()

    def is_duplicate(self, user_id: str, event_type: str, source_id: str) -> bool:
        """
        Check if a notification for this user, type, and source_id has been sent 
        in the last window_hours.
        """
        # PK=USER#<userId>, SK=NOTIFICATION#HIST#
        # Query latest notifications for user
        history = self.client.query_items(f'USER#{user_id}', 'NOTIFICATION#HIST#')
        # Filter for same source_id and within window
        recent = [
            n for n in history
            if n.get('source_id') == source_id and
               (datetime.utcnow() - datetime.fromisoformat(n.get('timestamp'))) < timedelta(hours=self.window_hours)
        ]
        return len(recent) > 0

    def should_rate_limit(self, user_id: str, limit_per_day: int = 10) -> bool:
        """
        Global rate limiting check.
        """
        history = self.client.query_items(f'USER#{user_id}', 'NOTIFICATION#HIST#')
        daily = [
            n for n in history
            if (datetime.utcnow() - datetime.fromisoformat(n.get('timestamp'))) < timedelta(days=1)
        ]
        return len(daily) >= limit_per_day
