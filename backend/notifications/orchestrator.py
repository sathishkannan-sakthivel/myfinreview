from typing import List, Dict, Any, Optional
from .models import NotificationEvent, NotificationType, NotificationPriority, DeliveryDecision, DeliveryChannel
from .prioritizer import NotificationPrioritizer
from .deduplicator import NotificationDeduplicator
from .channels import PushChannel, EmailChannel, TelegramChannel
from repositories.dynamo_client import DynamoClient
from datetime import datetime

class NotificationOrchestrator:
    def __init__(self):
        self.prioritizer = NotificationPrioritizer()
        self.deduplicator = NotificationDeduplicator()
        self.client = DynamoClient()
        self.channels = {
            DeliveryChannel.PUSH: PushChannel(),
            DeliveryChannel.EMAIL: EmailChannel(),
            DeliveryChannel.TELEGRAM: TelegramChannel()
        }

    def process_event(self, event: NotificationEvent, user_preferences: Dict[str, Any]) -> DeliveryDecision:
        # 1. Deduplication
        if self.deduplicator.is_duplicate(event.user_id, event.type.value, event.source_id):
            return DeliveryDecision(event.user_id, event.event_id, False, [], "Duplicate event within time window")

        # 2. Quiet Hours check (MVP: Mock user_preferences check)
        # user_preferences = { 'quiet_hours': {'start': '22:00', 'end': '08:00'}, 'enabled_channels': [PUSH, EMAIL] }
        if self._is_quiet_hours(user_preferences):
            # Only URGENT notifications break quiet hours
            if event.priority != NotificationPriority.URGENT:
                return DeliveryDecision(event.user_id, event.event_id, False, [], "Quiet hours enabled", is_digest=True)

        # 3. Rate Limiting
        if self.deduplicator.should_rate_limit(event.user_id):
            return DeliveryDecision(event.user_id, event.event_id, False, [], "Daily rate limit reached", is_digest=True)

        # 4. Delivery Decision based on priority
        should_deliver = self.prioritizer.should_deliver_immediately(event.priority)
        
        target_channels = user_preferences.get('enabled_channels', [DeliveryChannel.PUSH])
        if not should_deliver:
            return DeliveryDecision(event.user_id, event.event_id, False, target_channels, "Deferred for digest", is_digest=True)

        # 5. Persist Notification Record
        self._persist_notification(event)

        # 6. Execute Delivery
        for channel_type in target_channels:
            channel = self.channels.get(channel_type)
            if channel:
                channel.send(event.user_id, event)

        return DeliveryDecision(event.user_id, event.event_id, True, target_channels, "Delivered successfully")

    def _persist_notification(self, event: NotificationEvent):
        item = {
            'PK': f'USER#{event.user_id}',
            'SK': f'NOTIFICATION#HIST#{event.timestamp}#{event.event_id}',
            'type': event.type.value,
            'title': event.title,
            'message': event.message,
            'priority': event.priority.value,
            'source_id': event.source_id,
            'timestamp': event.timestamp,
            'metadata': event.metadata
        }
        self.client.put_item(item)

    def _is_quiet_hours(self, prefs: Dict[str, Any]) -> bool:
        # Mock logic
        current_hour = datetime.utcnow().hour
        if current_hour >= 22 or current_hour < 8:
            return prefs.get('enable_quiet_hours', True)
        return False
