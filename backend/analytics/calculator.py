from datetime import datetime
from typing import List, Dict
from .models import PortfolioAnalyticsInput, AnalyticsResult, CashFlow
from .xirr import calculate_xirr
from .concentration import calculate_concentration

class PortfolioAnalyticsCalculator:
    """
    Orchestrates calculation of XIRR and concentration without DB access.
    """
    def compute(self, input_data: PortfolioAnalyticsInput) -> AnalyticsResult:
        # 1. Calculate XIRR
        # Need to convert raw cashflows to the ones used by xirr logic if necessary
        # Assuming input_data.cashflows are already in the correct format.
        xirr_val = calculate_xirr(input_data.cashflows, input_data.current_valuation)
        
        # 2. Calculate Concentration
        concentration_data = calculate_concentration(input_data.holdings)
        
        # 3. Create Result
        return AnalyticsResult(
            user_id=input_data.user_id,
            portfolio_value=input_data.current_valuation,
            xirr=float(xirr_val),
            concentration_score=concentration_data.get('top_3_weight', 0.0),
            top_holdings=list(concentration_data.get('weights', {}).items())[:5],
            is_concentrated=concentration_data.get('is_concentrated', False),
            timestamp=datetime.utcnow().isoformat()
        )
