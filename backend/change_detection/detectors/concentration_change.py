from typing import List, Dict, Any
from ..models import ChangeEvent, ChangeType

class ConcentrationChangeDetector:
    def __init__(self, threshold_pt: float = 2.0):
        self.threshold_pt = threshold_pt

    def detect(self, prev_snapshot: Dict[str, Any], curr_snapshot: Dict[str, Any]) -> List[ChangeEvent]:
        events = []
        if not prev_snapshot or not curr_snapshot:
            return events

        prev_score = float(prev_snapshot.get('concentration_score', 0.0))
        curr_score = float(curr_snapshot.get('concentration_score', 0.0))

        drift = curr_score - prev_score

        if abs(drift) >= self.threshold_pt:
            direction = "increased" if drift > 0 else "decreased"
            impact = min(abs(drift), 10.0)

            events.append(ChangeEvent(
                type=ChangeType.CONCENTRATION,
                description=f"Portfolio concentration {direction} by {abs(drift):.2f}%",
                impact_score=impact,
                metadata={
                    "prev_score": prev_score,
                    "curr_score": curr_score,
                    "drift": drift
                }
            ))

        return events
