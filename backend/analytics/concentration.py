from typing import List, Dict

def calculate_concentration(holdings: List[Dict], threshold: float = 25.0) -> Dict:
    """
    Calculates weights for each holding and flags concentration.
    holdings: List of {symbol: str, value: float}
    """
    if not holdings:
        return {
            'weights': {},
            'top_3_weight': 0.0,
            'is_concentrated': False,
            'max_weight': 0.0,
            'max_symbol': None
        }
    
    total_value = sum(h.get('value', 0.0) for h in holdings)
    if total_value == 0:
        return {
            'weights': {},
            'top_3_weight': 0.0,
            'is_concentrated': False,
            'max_weight': 0.0,
            'max_symbol': None
        }

    weights = {}
    for h in holdings:
        symbol = h.get('symbol', 'UNKNOWN')
        weight = (h.get('value', 0.0) / total_value) * 100
        weights[symbol] = weight

    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    max_symbol, max_weight = sorted_weights[0] if sorted_weights else (None, 0.0)
    top_3_weight = sum(w for s, w in sorted_weights[:3])

    is_concentrated = (max_weight > threshold) or (top_3_weight > 50.0)

    return {
        'weights': weights,
        'top_3_weight': top_3_weight,
        'is_concentrated': is_concentrated,
        'max_weight': max_weight,
        'max_symbol': max_symbol
    }
