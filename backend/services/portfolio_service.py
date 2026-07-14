from repositories.holding_repository import HoldingRepository
from repositories.transaction_repository import TransactionRepository
from services.price_service import PriceService

class PortfolioService:
    def __init__(self):
        self.holding_repo = HoldingRepository()
        self.tx_repo = TransactionRepository()
        self.price_service = PriceService()

    def add_transaction(self, user_id, symbol, tx_type, quantity, price, timestamp=None):
        # 1. Record Transaction
        tx_data = {
            'type': tx_type,
            'quantity': float(quantity),
            'price': float(price),
            'timestamp': timestamp
        }
        self.tx_repo.record_transaction(user_id, symbol, tx_data)

        # 2. Update Holding (Average price calculation)
        holding = self.holding_repo.get_holding(user_id, symbol)
        if not holding:
            holding = {
                'symbol': symbol,
                'total_quantity': 0.0,
                'avg_price': 0.0,
                'current_valuation': 0.0,
                'gain_loss': 0.0,
                'gain_loss_pct': 0.0
            }

        total_qty = float(holding.get('total_quantity', 0.0))
        avg_price = float(holding.get('avg_price', 0.0))

        if tx_type == 'BUY':
            new_total_qty = total_qty + quantity
            new_avg_price = ((total_qty * avg_price) + (quantity * price)) / new_total_qty
        elif tx_type == 'SELL':
            new_total_qty = total_qty - quantity
            new_avg_price = avg_price # Avg price doesn't change on sell
        
        # 3. Update Valuation with Latest Price
        current_price = self.price_service.get_latest_price(symbol)
        if current_price:
            holding['total_quantity'] = new_total_qty
            holding['avg_price'] = new_avg_price
            holding['current_valuation'] = new_total_qty * current_price
            holding['gain_loss'] = holding['current_valuation'] - (new_total_qty * new_avg_price)
            if new_total_qty * new_avg_price > 0:
                holding['gain_loss_pct'] = (holding['gain_loss'] / (new_total_qty * new_avg_price)) * 100
            else:
                holding['gain_loss_pct'] = 0.0
        
        # Save updated holding
        self.holding_repo.save_holding(user_id, symbol, holding)
        return holding

    def get_portfolio_summary(self, user_id):
        holdings = self.holding_repo.get_user_holdings(user_id)
        
        # Refresh current prices for summary
        for holding in holdings:
            symbol = holding['symbol']
            price = self.price_service.get_latest_price(symbol)
            if price:
                holding['current_valuation'] = float(holding['total_quantity']) * price
                total_cost = float(holding['total_quantity']) * float(holding['avg_price'])
                holding['gain_loss'] = holding['current_valuation'] - total_cost
                holding['gain_loss_pct'] = (holding['gain_loss'] / total_cost * 100) if total_cost > 0 else 0
        
        total_valuation = sum(h.get('current_valuation', 0.0) for h in holdings)
        total_cost = sum(float(h.get('total_quantity', 0.0)) * float(h.get('avg_price', 0.0)) for h in holdings)
        
        summary = {
            'total_valuation': total_valuation,
            'total_cost': total_cost,
            'total_gain_loss': total_valuation - total_cost,
            'total_gain_loss_pct': ((total_valuation - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            'holdings': holdings
        }
        return summary
