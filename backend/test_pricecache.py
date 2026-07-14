from datetime import datetime
from sqlalchemy import select, func
from database import engine, Session
from models.portable_models import PriceCache

# Insert a new row
with Session(engine) as session:
    pc = PriceCache(symbol="TEST", price=123.45, timestamp=datetime.now())
    session.add(pc)
    session.commit()

# Query count
with Session(engine) as session:
    stmt = select(func.count()).select_from(PriceCache)
    count = session.exec(stmt).one()
    print("PriceCache row count after insert:", count)
