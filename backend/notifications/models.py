from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class NotificationType(Enum):
    ALERT = "ALERT"
    INSIGHT = "INSIGHT"
    REBALANCE = "REBALANCE"
    DAILY_DIGEST = "DAILY_DIGEST"

class NotificationPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class DeliveryChannel(Enum):
    PUSH = "PUSH"
    EMAIL = "EMAIL"
    TELEGRAM = "TELEGRAM"

@dataclass
class NotificationEvent:
    event_id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    source_id: str # Link to AlertEvent ID, Insight ID, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class DeliveryDecision:
    user_id: str
    event_id: str
    should_deliver: bool
    channels: List[DeliveryChannel]
    reason: str
    is_digest: bool = False

@dataclass
class NotificationDigest:
    user_id: str
    events: List[NotificationEvent]
    summary_text: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
