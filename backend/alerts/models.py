from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class AlertType(Enum):
    PRICE_THRESHOLD = "PRICE_THRESHOLD"
    ALLOCATION_DRIFT = "ALLOCATION_DRIFT"
    CONCENTRATION = "CONCENTRATION"
    PORTFOLIO_CHANGE = "PORTFOLIO_CHANGE"

class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class AlertRule:
    rule_id: str
    user_id: str
    type: AlertType
    symbol: Optional[str] = None
    threshold: float = 0.0
    target_value: Optional[float] = None
    severity: Severity = Severity.WARNING
    is_enabled: bool = True

@dataclass
class AlertEvent:
    event_id: str
    user_id: str
    rule_id: str
    type: AlertType
    message: str
    severity: Severity
    timestamp: str
    data: Dict = field(default_factory=dict)

@dataclass
class AlertEvaluationResult:
    events: List[AlertEvent] = field(default_factory=list)
