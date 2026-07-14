from typing import List, Optional
from ..models import AlertRule, AlertEvent, AlertType, Severity
import uuid
from datetime import datetime

class PriceAlertEvaluator:
    """
    Evaluates if a symbol's price has crossed a threshold.
    """
    def evaluate(self, rule: AlertRule, current_price: float) -> Optional[AlertEvent]:
        if not rule.is_enabled or rule.type != AlertType.PRICE_THRESHOLD:
            return None
        
        # Simple threshold check: if current_price >= rule.threshold (upper bound) 
        # OR if current_price <= rule.threshold (if specified for lower bound, need logic change)
        # For MVP, assume threshold is the price target to hit.
        
        if current_price >= rule.threshold:
            return AlertEvent(
                event_id=str(uuid.uuid4()),
                user_id=rule.user_id,
                rule_id=rule.rule_id,
                type=rule.type,
                message=f"Price of {rule.symbol} has reached threshold of {rule.threshold}. Current: {current_price}",
                severity=rule.severity,
                timestamp=datetime.utcnow().isoformat(),
                data={"symbol": rule.symbol, "current_price": current_price, "threshold": rule.threshold}
            )
        return None
