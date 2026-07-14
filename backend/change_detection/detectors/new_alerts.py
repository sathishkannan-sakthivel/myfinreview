from typing import List, Dict, Any
from ..models import ChangeEvent, ChangeType

class NewAlertsDetector:
    def detect(self, new_alerts: List[Dict[str, Any]]) -> List[ChangeEvent]:
        events = []
        for alert in new_alerts:
            severity = alert.get('severity', 'WARNING')
            impact = 8.0 if severity == 'CRITICAL' else 5.0
            
            events.append(ChangeEvent(
                type=ChangeType.ALERT,
                description=alert.get('message', 'New Alert Triggered'),
                impact_score=impact,
                metadata=alert
            ))
        return events
