from typing import List, Dict, Any
from .models import FundHolding, OverlapResult, EffectiveExposure
from .calculator import OverlapCalculator
from .provider import MockFundHoldingsProvider
from repositories.dynamo_client import DynamoClient

class OverlapEngine:
    def __init__(self):
        self.calculator = OverlapCalculator()
        self.provider = MockFundHoldingsProvider()
        self.client = DynamoClient()

    def generate_overlap_result(self, user_id: str) -> OverlapResult:
        # 1. Fetch user's mutual fund holdings from DynamoDB (PK=USER#<userId>, SK=HOLDING#)
        # Filter for funds specifically in a real app, assuming all holdings here for MVP
        all_holdings = self.client.query_items(f'USER#{user_id}', 'HOLDING#')
        
        # 2. Extract weights (normalize to 100 for this analysis)
        total_val = sum(h.get('current_valuation', 0) for h in all_holdings)
        if total_val == 0:
            return None
            
        fund_holdings = {
            h['symbol']: (h['current_valuation'] / total_val) * 100
            for h in all_holdings
        }

        # 3. Fetch underlying fund datasets
        fund_dataset = {}
        for fund_symbol in fund_holdings.keys():
            holdings = self.provider.get_fund_holdings(fund_symbol)
            if holdings:
                fund_dataset[fund_symbol] = holdings

        # 4. Calculate Overlap
        result = self.calculator.calculate_overlap(user_id, fund_holdings, fund_dataset)
        if not result:
            return None

        # 5. Store result in DynamoDB
        # PK=USER#<userId>, SK=OVERLAP#LATEST
        item = {
            'PK': f'USER#{user_id}',
            'SK': 'OVERLAP#LATEST',
            'timestamp': result.timestamp,
            'overlap_severity': result.overlap_severity,
            'total_overlap_score': float(result.total_overlap_score),
            'explanation_data': result.explanation_data,
            'effective_exposures': [
                {
                    'symbol': e.symbol,
                    'total_weight': float(e.total_weight),
                    'fund_count': len(e.contributing_funds)
                } for e in result.effective_exposures if len(e.contributing_funds) > 1
            ]
        }
        self.client.put_item(item)
        
        # History
        history_item = item.copy()
        history_item['SK'] = f"OVERLAP#HIST#{result.timestamp}"
        self.client.put_item(history_item)

        return result
