from database import engine
from sqlmodel import Session, select
from models.portable_models import PriceCache

with Session(engine) as s:
    rows = s.exec(select(PriceCache)).all()
    for r in rows[:5]:
        print(r.symbol, r.price, r.timestamp)
