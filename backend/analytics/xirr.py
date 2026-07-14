from datetime import date
from typing import List
from .models import CashFlow

def xnpv(rate: float, cashflows: List[CashFlow]) -> float:
    """
    Calculates Net Present Value for a series of irregular cash flows.
    """
    if not cashflows:
        return 0.0
    
    d0 = cashflows[0].date
    res = sum([
        cf.amount / (1.0 + rate) ** ((cf.date - d0).days / 365.0)
        for cf in cashflows
    ])
    return float(res.real if hasattr(res, 'real') else res)

def xirr_derivative(rate: float, cashflows: List[CashFlow]) -> float:
    """
    Calculates the derivative of XNPV with respect to the rate.
    """
    if not cashflows:
        return 0.0
    
    d0 = cashflows[0].date
    res = sum([
        -cf.amount * ((cf.date - d0).days / 365.0) * (1.0 + rate) ** (-(cf.date - d0).days / 365.0 - 1.0)
        for cf in cashflows
    ])
    return float(res.real if hasattr(res, 'real') else res)

def calculate_xirr(cashflows: List[CashFlow], current_valuation: float, guess: float = 0.1, max_iter: int = 100, tolerance: float = 1e-6) -> float:
    """
    Calculates the Internal Rate of Return for a series of irregular cash flows.
    Current valuation is treated as the final POSITIVE cash flow (liquidation).
    """
    if not cashflows:
        return 0.0
    
    # Clone and add current valuation as an INFLOW (positive cashflow) for IRR calculation
    full_cashflows = cashflows.copy()
    full_cashflows.append(CashFlow(amount=current_valuation, date=date.today()))
    
    # Ensure there is at least one positive and one negative cashflow
    amounts = [cf.amount for cf in full_cashflows]
    total_invested = sum([abs(a) for a in amounts if a < 0])
    
    if all(a >= 0 for a in amounts) or all(a <= 0 for a in amounts) or total_invested == 0:
        # Fallback to simple ROI if XIRR cannot be computed
        return 0.0

    rate = guess
    for _ in range(max_iter):
        try:
            f_val = xnpv(rate, full_cashflows)
            f_prime = xirr_derivative(rate, full_cashflows)
            
            if abs(f_prime) < tolerance:
                break
                
            new_rate = rate - f_val / f_prime
            
            # Handle potential complex numbers from the power operator
            if hasattr(new_rate, 'real'):
                new_rate = new_rate.real

            # Sanity check: XIRR cannot be less than -100%
            if new_rate <= -1.0:
                new_rate = -0.999

            if abs(new_rate - rate) < tolerance:
                return float(new_rate)
            
            rate = new_rate
        except (ZeroDivisionError, OverflowError, ValueError):
            break
        
    # Final Fallback: Simple ROI if XIRR fails to converge or produces an error
    total_gain = sum([cf.amount for cf in full_cashflows])
    simple_roi = float(total_gain / total_invested if total_invested > 0 else 0.0)
    
    # If the Newton result is suspiciously large or failed, return simple ROI
    final_rate = float(rate.real if hasattr(rate, 'real') else rate)
    if abs(final_rate) > 10.0 or rate == guess: # If > 1000% or never moved, likely an error
        return simple_roi
        
    return final_rate

