import sys
import os
import pytest
from sqlmodel import SQLModel, Session, create_engine

# add backend directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_dir = os.path.join(project_root, 'backend')
sys.path.append(backend_dir)

from services.portable_portfolio_service import PortablePortfolioService
from services.portable_price_service import PortablePriceService
from models.portable_models import User, Holding, Transaction
from datetime import datetime

# setup in-memory database
@pytest.fixture

def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess

class DummyPriceService:
    def __init__(self, session=None):
        pass
    async def get_prices_for_symbols(self, symbols):
        # simple fixed price mapping
        return {s: 100.0 for s in symbols}
    async def get_latest_price(self, symbol):
        return 100.0

@pytest.mark.asyncio
async def test_add_transaction_and_summary(session):
    # inject dummy price service
    service = PortablePortfolioService(session)
    service.price_service = DummyPriceService()

    # add user for completeness
    user = User(email="a@b.com", password="x")
    session.add(user)
    session.commit()
    session.refresh(user)

    # perform buy transaction
    holding = service.add_transaction(user.id, "ABC", "BUY", 10, 50.0)
    assert holding.quantity == 10
    assert pytest.approx(holding.avg_price) == 50.0

    # add another buy and ensure avg_price updates
    holding = service.add_transaction(user.id, "ABC", "BUY", 10, 150.0)
    assert holding.quantity == 20
    assert pytest.approx(holding.avg_price) == 100.0

    # compute summary asynchronously
    summary = await service.get_portfolio_summary(user.id)
    assert summary["total_valuation"] == 20 * 100.0
    assert summary["total_cost"] == 20 * 100.0
    assert summary["holdings"][0]["symbol"] == "ABC"

@pytest.mark.asyncio
async def test_tax_loss_candidate(session):
    service = PortablePortfolioService(session)
    service.price_service = DummyPriceService()

    user = User(email="c@d.com", password="y")
    session.add(user); session.commit(); session.refresh(user)

    service.add_transaction(user.id, "XYZ", "BUY", 10, 200.0)
    # manually adjust holding so price < cost
    from sqlmodel import select
    h = session.exec(
        select(Holding).where(Holding.user_id == user.id)
    ).one()
    h.quantity = 10
    h.avg_price = 200.0
    session.add(h); session.commit()

    summary = await service.get_portfolio_summary(user.id)
    # tax loss candidate logic is in analytics service; here verify raw values
    assert summary["holdings"][0]["current_price"] == 100.0
    assert summary["holdings"][0]["gain_loss"] < 0
