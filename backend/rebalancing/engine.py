from typing import List, Dict, Any
from .models import TargetAllocation, RebalancePlan
from .calculator import RebalancingCalculator
from repositories.dynamo_client import DynamoClient

class RebalancingEngine:
    def __init__(self):
        self.calculator = RebalancingCalculator()
        self.client = DynamoClient()

    def generate_plan(self, user_id: str, targets: List[TargetAllocation]) -> RebalancePlan:
        # 1. Fetch latest analytics snapshot
        analytics = self.client.get_item(f'USER#{user_id}', 'ANALYTICS#LATEST')
        if not analytics:
            return None

        # 2. Fetch latest prices for symbols in target
        prices = {}
        for target in targets:
            price_item = self.client.get_item(f'PRICE#{target.symbol}', 'LATEST')
            prices[target.symbol] = price_item.get('price', 1.0) if price_item else 1.0

        # 3. Calculate suggestions
        plan = self.calculator.calculate_suggestions(user_id, analytics, targets, prices)

        # 4. Store Plan in DynamoDB
        plan_item = {
            'PK': f'USER#{user_id}',
            'SK': 'REBALANCE#LATEST',
            'timestamp': plan.timestamp,
            'total_valuation': float(plan.total_valuation),
            'drift_severity': plan.drift_severity,
            'explanation_data': plan.explanation_data,
            'suggestions': [
                {
                    'symbol': s.symbol,
                    'current_weight': s.current_weight,
                    'target_weight': s.target_weight,
                    'action': s.suggested_action,
                    'quantity': float(s.suggested_quantity),
                    'price': float(s.current_price)
                } for s in plan.suggestions
            ]
        }
        self.client.put_item(plan_item)
        
        # Also store in history
        history_item = plan_item.copy()
        history_item['SK'] = f"REBALANCE#HIST#{plan.timestamp}"
        self.client.put_item(history_item)

        return plan

    def compute_drift(self, user_id: str, targets: List[TargetAllocation]) -> dict:
        """Return diagnostic metrics without generating buy/sell instructions."""
        analytics = self.client.get_item(f'USER#{user_id}', 'ANALYTICS#LATEST')
        if not analytics:
            return {'error': 'no analytics available'}

        prices = {}
        for target in targets:
            price_item = self.client.get_item(f'PRICE#{target.symbol}', 'LATEST')
            prices[target.symbol] = price_item.get('price', 1.0) if price_item else 1.0

        plan = self.calculator.calculate_suggestions(user_id, analytics, targets, prices)
        # return only drift severity and weight breakdown
        return {
            'timestamp': plan.timestamp,
            'drift_severity': plan.drift_severity,
            'current_weights': {s.symbol: s.current_weight for s in plan.suggestions},
            'target_weights': {s.symbol: s.target_weight for s in plan.suggestions}
        }
