from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class FundHolding:
    symbol: str # The stock symbol within the fund
    weight: float # percentage of the fund

@dataclass
class EffectiveExposure:
    symbol: str
    total_weight: float # total weight in user's portfolio across all funds
    contributing_funds: List[Dict[str, Any]] # List of {fund_symbol: str, weight_contribution: float}

@dataclass
class OverlapResult:
    user_id: str
    timestamp: str
    effective_exposures: List[EffectiveExposure]
    overlap_severity: str # LOW, MEDIUM, HIGH
    total_overlap_score: float
    explanation_data: Dict = field(default_factory=dict)
