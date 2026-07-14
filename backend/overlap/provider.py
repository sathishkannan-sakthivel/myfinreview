from abc import ABC, abstractmethod
from typing import List, Dict
from .models import FundHolding

class BaseFundHoldingsProvider(ABC):
    @abstractmethod
    def get_fund_holdings(self, fund_symbol: str) -> List[FundHolding]:
        pass

class MockFundHoldingsProvider(BaseFundHoldingsProvider):
    """
    Initial implementation using mock dataset.
    Can be replaced by real Mutual Fund API (like Value Research or Morningstar API).
    """
    def __init__(self):
        # Mock data for some Indian Mutual Funds
        self.dataset = {
            "MIRA_ASSET_LARGECAP": [
                FundHolding("HDFCBANK", 9.2),
                FundHolding("ICICIBANK", 8.5),
                FundHolding("RELIANCE", 7.8),
                FundHolding("INFY", 4.5),
                FundHolding("TCS", 3.2)
            ],
            "AXIS_BLUECHIP": [
                FundHolding("HDFCBANK", 8.8),
                FundHolding("ICICIBANK", 9.1),
                FundHolding("BAJFINANCE", 6.5),
                FundHolding("INFY", 5.2),
                FundHolding("RELIANCE", 4.8)
            ],
            "SBI_FOCUS_EQUITY": [
                FundHolding("HDFCBANK", 7.5),
                FundHolding("RELIANCE", 8.2),
                FundHolding("MUTHOOTFIN", 5.5),
                FundHolding("ICICIBANK", 4.8),
                FundHolding("BHARTIARTL", 4.2)
            ]
        }

    def get_fund_holdings(self, fund_symbol: str) -> List[FundHolding]:
        # Simple lookup with default
        return self.dataset.get(fund_symbol, [])
