from abc import ABC, abstractmethod
from .models import NotificationEvent, DeliveryChannel

class BaseChannel(ABC):
    @property
    @abstractmethod
    def channel_type(self) -> DeliveryChannel:
        pass

    @abstractmethod
    def send(self, user_id: str, event: NotificationEvent) -> bool:
        pass

class PushChannel(BaseChannel):
    channel_type = DeliveryChannel.PUSH
    def send(self, user_id: str, event: NotificationEvent) -> bool:
        print(f"[PUSH] Sending to {user_id}: {event.title}")
        return True

class EmailChannel(BaseChannel):
    channel_type = DeliveryChannel.EMAIL
    def send(self, user_id: str, event: NotificationEvent) -> bool:
        print(f"[EMAIL] Sending to {user_id}: {event.title}")
        return True

class TelegramChannel(BaseChannel):
    channel_type = DeliveryChannel.TELEGRAM
    def send(self, user_id: str, event: NotificationEvent) -> bool:
        # Placeholder for Telegram implementation
        print(f"[TELEGRAM] (Mock) Sending to {user_id}: {event.title}")
        return True
