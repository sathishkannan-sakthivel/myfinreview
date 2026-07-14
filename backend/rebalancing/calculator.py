from typing import List, Dict, Any
from .models import TargetAllocation, RebalanceSuggestion, RebalancePlan
from datetime import datetime

class RebalancingCalculator:
    def __init__(self, tolerance_band: float = 2.0):
        self.tolerance_band = tolerance_band # ignore drift < 2%

    def calculate_suggestions(self, user_id: str, analytics_snapshot: Dict[str, Any], targets: List[TargetAllocation], current_prices: Dict[str, float]) -> RebalancePlan:
        total_value = float(analytics_snapshot.get('portfolio_value', 0.0))
        if total_value == 0:
            return RebalancePlan(user_id, datetime.utcnow().isoformat(), 0, [], "INFO")

        # Get weights from analytics: top_holdings is List of (symbol, weight)
        weights = {h[0]: h[1] for h in analytics_snapshot.get('top_holdings', [])}
        
        suggestions = []
        max_drift = 0.0

        for target in targets:
            symbol = target.symbol
            curr_weight = float(weights.get(symbol, 0.0))
            target_weight = target.target_weight
            drift = curr_weight - target_weight
            max_drift = max(max_drift, abs(drift))

            if abs(drift) >= self.tolerance_band:
                required_change = ((target_weight - curr_weight) / 100.0) * total_value
                price = current_prices.get(symbol, 1.0) 

                suggestions.append(RebalanceSuggestion(
                    symbol=symbol,
                    current_weight=curr_weight,
                    target_weight=target_weight,
                    required_value_change=required_change,
                    suggested_action="DIAGNOSTIC",
                    suggested_quantity=0,
                    current_price=price,
                    drift=drift
                ))

        severity = "INFO"
        if max_drift > 10.0:
            severity = "CRITICAL"
        elif max_drift > 5.0:
            severity = "WARNING"

        return RebalancePlan(
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            total_valuation=total_value,
            suggestions=suggestions,
            drift_severity=severity,
            explanation_data={
                "max_drift": max_drift,
                "tolerance_band": self.tolerance_band,
                "count": len(suggestions)
            }
        )
