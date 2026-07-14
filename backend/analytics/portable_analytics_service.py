from sqlmodel import Session, select
from models.portable_models import Holding, Transaction, AnalyticsSummary, TransactionType, User
from datetime import date, datetime
from typing import List, Optional
from config import settings
import json
from .xirr import calculate_xirr, CashFlow as XIRRCashFlow

class CashFlow:
    def __init__(self, amount: float, date: date):
        self.amount = amount
        self.date = date

class PortableAnalyticsService:
    def __init__(self, session: Session):
        self.session = session

    def calculate_and_save_summary(self, user_id: int, current_valuation: float, holdings_data: List[dict]):
        # 1. Gather Data
        transactions = self.session.exec(select(Transaction).where(Transaction.user_id == user_id)).all()
        user = self.session.get(User, user_id)

        # 2. XIRR and Cost Calculation
        xirr_val, real_cost = self._calculate_xirr_and_cost(transactions, current_valuation)
        
        # 3. Concentration (Individual Asset > 25% threshold)
        concentration_score, is_concentrated, concentrated_symbols = self._calculate_concentration(holdings_data, current_valuation)

        # 4. Drift Analysis (Current vs Target Allocation)
        drift_data = []
        if user and user.target_allocation:
            try:
                target_alloc = json.loads(user.target_allocation)
                for symbol, target_pct in target_alloc.items():
                    # Find current weight
                    h = next((h for h in holdings_data if h.get('symbol') == symbol), None)
                    h_val = h.get('current_valuation', 0) if h else 0
                    current_weight = (h_val / current_valuation * 100) if current_valuation > 0 else 0
                    drift_data.append({
                        "symbol": symbol,
                        "target_pct": target_pct,
                        "current_pct": current_weight,
                        "drift": current_weight - target_pct
                    })
            except Exception as e:
                print(f"ERROR: Drift analysis failed for user {user_id}: {e}")

        # 5. Tax-Loss Diagnostic (PREMIUM)
        tax_loss_candidates = []
        for h in holdings_data:
            if h.get('current_valuation', 0) < (h.get('total_quantity', 0) * h.get('avg_price', 0)):
                tax_loss_candidates.append(h.get('symbol'))

        # 6. Save
        summary = AnalyticsSummary(
            user_id=user_id,
            total_valuation=current_valuation,
            total_cost=real_cost,
            xirr=float(xirr_val) * 100, # Convert to percentage for display
            concentration_score=concentration_score,
            is_concentrated=is_concentrated,
            data_json=json.dumps({
                "tax_loss_candidates": tax_loss_candidates,
                "drift_analysis": drift_data,
                "concentrated_symbols": concentrated_symbols
            }),
            timestamp=datetime.utcnow()
        )
        self.session.add(summary)
        self.session.commit()
        self.session.refresh(summary)
        return summary

    def _calculate_xirr_and_cost(self, transactions: List[Transaction], current_valuation: float):
        if not transactions:
            return 0.0, 0.0
        
        cashflows = []
        total_investment = 0.0
        
        for t in transactions:
            amt = float(t.quantity * t.price)
            # In XIRR: Investment (outflow) is negative, Withdrawal (inflow) is positive
            if t.type == TransactionType.BUY:
                cashflows.append(XIRRCashFlow(amount=-amt, date=t.date.date()))
                total_investment += amt
            else:
                cashflows.append(XIRRCashFlow(amount=amt, date=t.date.date()))
                total_investment -= amt # Reducing cost basis for sells

        # Valuation is a positive inflow (if liquidated today)
        xirr_val = calculate_xirr(cashflows, current_valuation)
        
        return xirr_val, total_investment

    def _calculate_xirr(self, transactions: List[Transaction], current_valuation: float) -> float:
        # Legacy method kept for safety but redirected
        val, _ = self._calculate_xirr_and_cost(transactions, current_valuation)
        return val * 100


    def _calculate_concentration(self, holdings_data: List[dict], total_valuation: float):
        if total_valuation <= 0 or not holdings_data:
            return 0.0, False, []
        
        # Sort holdings by weight
        holdings_with_weights = sorted([
            (h.get('symbol'), (h.get('current_valuation', 0) / total_valuation * 100)) 
            for h in holdings_data
        ], key=lambda x: x[1], reverse=True)
        
        top_3_weight = sum(w[1] for w in holdings_with_weights[:3])
        
        # Identify individual symbols exceeding the 25% threshold (as per changes-needed.txt)
        concentrated_symbols = [
            s for s, w in holdings_with_weights if w > settings.CONCENTRATION_THRESHOLD_PCT
        ]
        
        is_concentrated = (len(concentrated_symbols) > 0) or (top_3_weight > 50.0) # High overall concentration
        return top_3_weight, is_concentrated, concentrated_symbols

    def get_latest_summary(self, user_id: int):
        statement = select(AnalyticsSummary).where(AnalyticsSummary.user_id == user_id).order_by(AnalyticsSummary.timestamp.desc())
        return self.session.exec(statement).first()
