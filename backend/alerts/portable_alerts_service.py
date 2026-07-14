from sqlmodel import Session, select
from models.portable_models import AlertRule, AlertEvent, Holding, User
from services.portable_price_service import PortablePriceService
from datetime import datetime
import json

class PortableAlertsService:
    def __init__(self, session: Session):
        self.session = session
        self.price_service = PortablePriceService(session)

    def add_rule(self, user_id: int, alert_type: str, symbol: str = None, threshold: float = 0.0, target_value: float = None):
        rule = AlertRule(
            user_id=user_id,
            type=alert_type,
            symbol=symbol,
            threshold=threshold,
            target_value=target_value
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def get_rules(self, user_id: int):
        statement = select(AlertRule).where(AlertRule.user_id == user_id, AlertRule.is_enabled == True)
        return self.session.exec(statement).all()

    def evaluate_all_rules(self, user_id: int):
        """
        Runs the evaluation engine for a specific user.
        """
        print(f"DEBUG: Evaluating alerts for user {user_id}...")
        rules = self.get_rules(user_id)
        user = self.session.get(User, user_id)
        
        holdings = self.session.exec(select(Holding).where(Holding.user_id == user_id)).all()
        
        # 1. Gather all symbols
        symbols_to_check = set(h.symbol for h in holdings)
        for r in rules:
            if r.symbol: symbols_to_check.add(r.symbol)
        
        # Add symbols from target allocation
        target_alloc = {}
        if user and user.target_allocation:
            try:
                target_alloc = json.loads(user.target_allocation)
                for s in target_alloc.keys(): symbols_to_check.add(s)
            except: pass

        # 2. Get latest prices (from cache, sync method)
        prices = {}
        for symbol in symbols_to_check:
            cached = self.price_service.get_latest_price_data(symbol)
            prices[symbol] = cached.price if cached else None
        
        # 3. Calculate portfolio context
        total_valuation = sum(h.quantity * (prices.get(h.symbol) or 0.0) for h in holdings)
        allocation = {h.symbol: (h.quantity * (prices.get(h.symbol) or 0.0) / total_valuation * 100) if total_valuation > 0 else 0.0 for h in holdings}

        new_events = []
        
        # 4. Evaluate explicitly set rules
        for rule in rules:
            event = self._evaluate_rule(rule, prices, allocation, total_valuation)
            if event:
                self.session.add(event)
                new_events.append(event)
        
        # 5. AUTOMATIC DRIFT EVALUATION (From Target Allocation)
        sensitivity = getattr(user, 'drift_sensitivity', 5.0) if user else 5.0
        for symbol, target_pct in target_alloc.items():
            actual_pct = allocation.get(symbol, 0.0)
            drift = abs(actual_pct - target_pct)
            if drift >= sensitivity: 
                event = AlertEvent(
                    user_id=user_id,
                    rule_id=None, # System generated
                    type="ALLOCATION_DRIFT",
                    message=f"System Drift Alert: {symbol} is {actual_pct:.1f}% (Target: {target_pct}%, Drift: {drift:.1f}%)",
                    severity="CRITICAL" if drift > (sensitivity * 2) else "WARNING",
                    data_json=json.dumps({"symbol": symbol, "drift": drift})
                )
                self.session.add(event)
                new_events.append(event)
        
        if new_events:
            self.session.commit()
            for e in new_events:
                self.session.refresh(e)
        
        return new_events

    def _evaluate_rule(self, rule: AlertRule, prices: dict, allocation: dict, total_valuation: float):
        # Handle Price Alerts (Above/Below)
        if rule.type in ["PRICE_THRESHOLD", "PRICE_ABOVE", "PRICE_BELOW"]:
            price = prices.get(rule.symbol)
            if not price: return None

            triggered = False
            if rule.type == "PRICE_ABOVE" and price >= rule.threshold: triggered = True
            elif rule.type == "PRICE_BELOW" and price <= rule.threshold: triggered = True
            elif rule.type == "PRICE_THRESHOLD" and price >= rule.threshold: triggered = True

            if triggered:
                return AlertEvent(
                    user_id=rule.user_id,
                    rule_id=rule.id,
                    type=rule.type,
                    message=f"Signal: {rule.symbol} is at ₹{price:.2f} ({rule.type.replace('_',' ')} ₹{rule.threshold})",
                    severity="WARNING",
                    data_json=json.dumps({"current_price": price, "symbol": rule.symbol})
                )
        
        # Handle Portfolio Valuation Alerts
        elif rule.type == "VALUATION_BELOW":
            if total_valuation > 0 and total_valuation <= rule.threshold:
                return AlertEvent(
                    user_id=rule.user_id,
                    rule_id=rule.id,
                    type=rule.type,
                    message=f"Alert: Portfolio valuation ₹{total_valuation:,.2f} dropped below threshold ₹{rule.threshold:,.2f}",
                    severity="CRITICAL",
                    data_json=json.dumps({"total_valuation": total_valuation})
                )

        elif rule.type == "ALLOCATION_DRIFT":
            actual_weight = allocation.get(rule.symbol, 0.0)
            target = rule.target_value or 0.0
            if abs(actual_weight - target) >= rule.threshold:
                return AlertEvent(
                    user_id=rule.user_id,
                    rule_id=rule.id,
                    type=rule.type,
                    message=f"Drift: {rule.symbol} allocation is {actual_weight:.2f}% (Target: {target}%)",
                    severity="CRITICAL" if abs(actual_weight - target) > 10 else "WARNING",
                    data_json=json.dumps({"symbol": rule.symbol, "drift": abs(actual_weight-target)})
                )
        
        return None

    def get_recent_events(self, user_id: int, limit: int = 10):
        statement = select(AlertEvent).where(AlertEvent.user_id == user_id).order_by(AlertEvent.timestamp.desc()).limit(limit)
        return self.session.exec(statement).all()
