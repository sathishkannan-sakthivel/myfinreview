from typing import List, Dict, Any
from ..models import ChangeEvent, ChangeType

class AllocationChangeDetector:
    def __init__(self, threshold_pt: float = 2.0):
        self.threshold_pt = threshold_pt # Threshold in percentage points

    def detect(self, prev_snapshot: Dict[str, Any], curr_snapshot: Dict[str, Any]) -> List[ChangeEvent]:
        events = []
        if not prev_snapshot or not curr_snapshot:
            return events

        # top_holdings is List of (symbol, weight)
        prev_weights = {h[0]: h[1] for h in prev_snapshot.get('top_holdings', [])}
        curr_weights = {h[0]: h[1] for h in curr_snapshot.get('top_holdings', [])}

        all_symbols = set(prev_weights.keys()) | set(curr_weights.keys())

        for symbol in all_symbols:
            prev_w = prev_weights.get(symbol, 0.0)
            curr_w = curr_weights.get(symbol, 0.0)
            drift = curr_w - prev_w

            if abs(drift) >= self.threshold_pt:
                direction = "increased" if drift > 0 else "decreased"
                impact = min(abs(drift) / 2.0, 10.0) # Scaled impact

                events.append(ChangeEvent(
                    type=ChangeType.ALLOCATION,
                    description=f"Weight of {symbol} {direction} by {abs(drift):.2f}%",
                    impact_score=impact,
                    metadata={
                        "symbol": symbol,
                        "prev_weight": prev_w,
                        "curr_weight": curr_w,
                        "drift": drift
                    }
                ))

        return events
