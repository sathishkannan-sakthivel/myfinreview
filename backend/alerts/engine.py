from typing import List, Dict, Any
from .models import AlertRule, AlertEvent, AlertType, AlertEvaluationResult
from .evaluators.price_alert import PriceAlertEvaluator
from .evaluators.allocation_drift import AllocationDriftEvaluator
from .evaluators.concentration_alert import ConcentrationAlertEvaluator
from .evaluators.portfolio_change import PortfolioChangeEvaluator

class AlertsEngine:
    def __init__(self):
        self.price_evaluator = PriceAlertEvaluator()
        self.drift_evaluator = AllocationDriftEvaluator()
        self.concentration_evaluator = ConcentrationAlertEvaluator()
        self.change_evaluator = PortfolioChangeEvaluator()

    def evaluate_rules(self, rules: List[AlertRule], context: Dict[str, Any]) -> AlertEvaluationResult:
        """
        context: {
            'prices': { 'SYMBOL': float },
            'allocation': { 'SYMBOL': float },
            'concentration_score': float,
            'portfolio_change_pct': float
        }
        """
        result = AlertEvaluationResult()
        
        for rule in rules:
            event = None
            if rule.type == AlertType.PRICE_THRESHOLD:
                price = context.get('prices', {}).get(rule.symbol)
                if price:
                    event = self.price_evaluator.evaluate(rule, price)
            
            elif rule.type == AlertType.ALLOCATION_DRIFT:
                actual_weight = context.get('allocation', {}).get(rule.symbol, 0.0)
                event = self.drift_evaluator.evaluate(rule, actual_weight)
            
            elif rule.type == AlertType.CONCENTRATION:
                score = context.get('concentration_score', 0.0)
                event = self.concentration_evaluator.evaluate(rule, score)
                
            elif rule.type == AlertType.PORTFOLIO_CHANGE:
                change_pct = context.get('portfolio_change_pct', 0.0)
                event = self.change_evaluator.evaluate(rule, change_pct)
            
            if event:
                result.events.append(event)
                
        return result
