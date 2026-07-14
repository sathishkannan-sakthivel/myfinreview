from typing import List, Optional, Dict, Any
from ..models import ChangeEvent, ChangeType

class ValueChangeDetector:
    def __init__(self, threshold_pct: float = 1.0):
        self.threshold_pct = threshold_pct

    def detect(self, prev_snapshot: Dict[str, Any], curr_snapshot: Dict[str, Any]) -> List[ChangeEvent]:
        events = []
        if not prev_snapshot or not curr_snapshot:
            return events

        prev_val = float(prev_snapshot.get('portfolio_value', 0.0))
        curr_val = float(curr_snapshot.get('portfolio_value', 0.0))

        if prev_val == 0:
            return events

        change_pct = ((curr_val - prev_val) / prev_val) * 100
        
        if abs(change_pct) >= self.threshold_pct:
            direction = "increased" if change_pct > 0 else "decreased"
            impact = min(abs(change_pct), 10.0) # Cap impact score at 10
            
            events.append(ChangeEvent(
                type=ChangeType.VALUE,
                description=f"Portfolio value {direction} by {abs(change_pct):.2f}%",
                impact_score=impact,
                metadata={
                    "prev_value": prev_val,
                    "curr_value": curr_val,
                    "change_pct": change_pct
                }
            ))
            
        return events
