from typing import Optional
from ..models import AlertRule, AlertEvent, AlertType
import uuid
from datetime import datetime

class PortfolioChangeEvaluator:
    def evaluate(self, rule: AlertRule, change_pct: float) -> Optional[AlertEvent]:
        if not rule.is_enabled or rule.type != AlertType.PORTFOLIO_CHANGE:
            return None
        
        if abs(change_pct) >= rule.threshold:
            direction = "gain" if change_pct >= 0 else "loss"
            return AlertEvent(
                event_id=str(uuid.uuid4()),
                user_id=rule.user_id,
                rule_id=rule.rule_id,
                type=rule.type,
                message=f"Significant portfolio {direction} detected: {change_pct:.2f}%. Threshold: {rule.threshold}%",
                severity=rule.severity,
                timestamp=datetime.utcnow().isoformat(),
                data={"change_pct": change_pct, "threshold": rule.threshold}
            )
        return None
