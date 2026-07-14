from sqlmodel import Session, select
from repositories.portable_repository import PortableHoldingRepository, PortableTransactionRepository
from services.portable_price_service import PortablePriceService
from models.portable_models import Holding, Transaction, PriceCache
from datetime import datetime
import hashlib

class PortablePortfolioService:
    def __init__(self, session: Session):
        self.holding_repo = PortableHoldingRepository(session)
        self.tx_repo = PortableTransactionRepository(session)
        self.price_service = PortablePriceService(session)

    def add_transaction(self, user_id: int, symbol: str, tx_type: str, quantity: float, price: float, date: datetime = None, name: str = None) -> Holding:
        # 1. Generate Composite Hash for Upsert (Date + Symbol + Quantity + Price)
        tx_date = date or datetime.now()
        date_str = tx_date.strftime('%Y-%m-%d')
        tx_hash = hashlib.md5(f"{user_id}:{date_str}:{symbol}:{tx_type}:{quantity}:{price}".encode()).hexdigest()

        # 2. Record Transaction
        transaction = Transaction(
            user_id=user_id,
            symbol=symbol,
            type=tx_type,
            quantity=float(quantity),
            price=float(price),
            date=tx_date,
            hash=tx_hash
        )
        existing = self.tx_repo.record_transaction(transaction)
        if existing and existing.id != transaction.id:
            # Transaction already exists, skip updating holding if this was a duplicate
            return self.holding_repo.get_holding(user_id, symbol)

        # 3. Update Global Metadata (Name) if provided, but DO NOT overwrite market price
        if name:
            self.price_service.update_asset_name(symbol, name)

        # 3. Update Holding (Average price calculation)
        holding = self.holding_repo.get_holding(user_id, symbol)
        if not holding:
            holding = Holding(
                user_id=user_id,
                symbol=symbol,
                quantity=0.0,
                avg_price=0.0,
                asset_type='MF' if str(symbol).isdigit() else 'STOCK'
            )
        
        total_qty = holding.quantity
        avg_price = holding.avg_price

        if tx_type == 'BUY':
            new_total_qty = total_qty + quantity
            new_avg_price = ((total_qty * avg_price) + (quantity * price)) / new_total_qty
        elif tx_type == 'SELL':
            new_total_qty = total_qty - quantity
            new_avg_price = avg_price
        
        holding.quantity = new_total_qty
        holding.avg_price = new_avg_price
        holding.last_updated = datetime.now()
        
        self.holding_repo.save_holding(holding)
        return holding

    async def get_portfolio_summary(self, user_id: int):
        holdings = self.holding_repo.get_user_holdings(user_id)
        if not holdings:
            return {'total_valuation': 0, 'total_cost': 0, 'total_gain_loss': 0, 'total_gain_loss_pct': 0, 'holdings': []}

        symbols = [h.symbol for h in holdings]
        price_map = await self.price_service.get_prices_for_symbols(symbols)
        
        statement = select(PriceCache).where(PriceCache.symbol.in_(symbols))
        metadata_items = self.holding_repo.session.exec(statement).all()
        name_map = {m.symbol: m.name for m in metadata_items if m.name}

        results = []
        total_valuation = 0.0
        total_cost = 0.0

        for holding in holdings:
            symbol = holding.symbol
            current_price = price_map.get(symbol)
            asset_name = name_map.get(symbol) or symbol
            
            h_data = {
                "symbol": symbol,
                "name": asset_name,
                "total_quantity": holding.quantity,
                "avg_price": holding.avg_price,
                "asset_type": holding.asset_type
            }
            
            if current_price and current_price > 0:
                h_data['current_price'] = current_price
                h_data['current_valuation'] = float(holding.quantity) * current_price
                h_cost = float(holding.quantity) * float(holding.avg_price)
                h_data['gain_loss'] = h_data['current_valuation'] - h_cost
                h_data['gain_loss_pct'] = (h_data['gain_loss'] / h_cost * 100) if h_cost > 0 else 0
                
                total_valuation += h_data['current_valuation']
                total_cost += h_cost
            
            results.append(h_data)
        
        return {
            'total_valuation': total_valuation,
            'total_cost': total_cost,
            'total_gain_loss': total_valuation - total_cost,
            'total_gain_loss_pct': ((total_valuation - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            'holdings': results
        }
