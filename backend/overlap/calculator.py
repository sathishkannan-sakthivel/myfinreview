from typing import List, Dict, Any
from .models import FundHolding, EffectiveExposure, OverlapResult
from datetime import datetime

class OverlapCalculator:
    """
    Computes effective exposure per stock and overlap severity across funds.
    """
    def __init__(self, high_exposure_threshold: float = 10.0):
        self.high_exposure_threshold = high_exposure_threshold

    def calculate_overlap(self, user_id: str, fund_holdings: Dict[str, float], fund_dataset: Dict[str, List[FundHolding]]) -> OverlapResult:
        """
        fund_holdings: Dict of {fund_symbol: weight_in_user_portfolio}
        fund_dataset: Dict of {fund_symbol: List[FundHolding]}
        """
        # Aggregate underlying stock exposure
        stock_agg = {} # symbol -> {total_weight: float, contributing_funds: []}
        
        total_fund_weight = sum(fund_holdings.values())
        if total_fund_weight == 0:
            return None

        for fund_symbol, fund_weight in fund_holdings.items():
            holdings = fund_dataset.get(fund_symbol, [])
            for h in holdings:
                # Effective weight in portfolio = (weight of fund in portfolio) * (weight of stock in fund)
                # Note: Assuming fund_weight is normalized to sum to 100 for this analysis
                eff_weight = (fund_weight / 100.0) * h.weight
                
                if h.symbol not in stock_agg:
                    stock_agg[h.symbol] = {"total_weight": 0.0, "contributing_funds": []}
                
                stock_agg[h.symbol]["total_weight"] += eff_weight
                stock_agg[h.symbol]["contributing_funds"].append({
                    "fund_symbol": fund_symbol,
                    "weight_contribution": eff_weight
                })

        effective_exposures = [
            EffectiveExposure(
                symbol=s,
                total_weight=v["total_weight"],
                contributing_funds=v["contributing_funds"]
            )
            for s, v in stock_agg.items()
        ]
        
        # Sort by total_weight descending
        effective_exposures.sort(key=lambda x: x.total_weight, reverse=True)

        # Detect Overlap Severity
        # total_overlap_score: sum of weights of stocks held in >1 fund
        overlap_score = sum(e.total_weight for e in effective_exposures if len(e.contributing_funds) > 1)
        
        severity = "LOW"
        if overlap_score > 40:
            severity = "HIGH"
        elif overlap_score > 20:
            severity = "MEDIUM"

        return OverlapResult(
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            effective_exposures=effective_exposures,
            overlap_severity=severity,
            total_overlap_score=overlap_score,
            explanation_data={
                "top_hidden_exposures": [
                    {"symbol": e.symbol, "total_weight": e.total_weight, "fund_count": len(e.contributing_funds)}
                    for e in effective_exposures[:5] if len(e.contributing_funds) > 1
                ],
                "total_funds_analyzed": len(fund_holdings)
            }
        )
