from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict

@dataclass
class CashFlow:
    amount: float  # Negative for buy, positive for sell
    date: date

@dataclass
class PortfolioAnalyticsInput:
    user_id: str
    current_valuation: float
    cashflows: List[CashFlow]
    holdings: List[Dict] # List of {symbol: str, value: float}

@dataclass
class AnalyticsResult:
    user_id: str
    portfolio_value: float
    xirr: float
    concentration_score: float
    top_holdings: List[Dict]
    is_concentrated: bool
    timestamp: str
