from typing import Optional
from ..models import AlertRule, AlertEvent, AlertType
import uuid
from datetime import datetime

class AllocationDriftEvaluator:
    def evaluate(self, rule: AlertRule, actual_weight: float) -> Optional[AlertEvent]:
        if not rule.is_enabled or rule.type != AlertType.ALLOCATION_DRIFT:
            return None
        
        target = rule.target_value or 0.0
        drift_threshold = rule.threshold
        
        if abs(actual_weight - target) >= drift_threshold:
            return AlertEvent(
                event_id=str(uuid.uuid4()),
                user_id=rule.user_id,
                rule_id=rule.rule_id,
                type=rule.type,
                message=f"Allocation drift detected for {rule.symbol}. Target: {target}%, Actual: {actual_weight:.2f}% (Drift: {abs(actual_weight-target):.2f}%)",
                severity=rule.severity,
                timestamp=datetime.utcnow().isoformat(),
                data={"symbol": rule.symbol, "actual_weight": actual_weight, "target_weight": target, "drift": abs(actual_weight-target)}
            )
        return None
