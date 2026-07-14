from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class TargetAllocation:
    symbol: str
    target_weight: float # percentage

@dataclass
class RebalanceSuggestion:
    symbol: str
    current_weight: float
    target_weight: float
    required_value_change: float
    suggested_action: str # BUY, SELL, ADJUST_SIP
    suggested_quantity: float
    current_price: float
    drift: float # percentage point difference

@dataclass
class RebalancePlan:
    user_id: str
    timestamp: str
    total_valuation: float
    suggestions: List[RebalanceSuggestion]
    drift_severity: str # INFO, WARNING, CRITICAL
    explanation_data: Dict = field(default_factory=dict)
