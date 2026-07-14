from typing import Optional
from ..models import AlertRule, AlertEvent, AlertType
import uuid
from datetime import datetime

class ConcentrationAlertEvaluator:
    def evaluate(self, rule: AlertRule, concentration_score: float) -> Optional[AlertEvent]:
        if not rule.is_enabled or rule.type != AlertType.CONCENTRATION:
            return None
        
        if concentration_score >= rule.threshold:
            return AlertEvent(
                event_id=str(uuid.uuid4()),
                user_id=rule.user_id,
                rule_id=rule.rule_id,
                type=rule.type,
                message=f"High portfolio concentration detected: {concentration_score:.2f}%. Threshold: {rule.threshold}%",
                severity=rule.severity,
                timestamp=datetime.utcnow().isoformat(),
                data={"concentration_score": concentration_score, "threshold": rule.threshold}
            )
        return None
