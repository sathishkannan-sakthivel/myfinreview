from database import engine, init_db
from sqlmodel import Session, select
from models.portable_models import NewsArticle, Holding, AlertRule

init_db()
with Session(engine) as s:
    print('holdings now:')
    print(s.exec(select(Holding)).all())
    print('alerts rules:')
    print(s.exec(select(AlertRule)).all())
    print('news articles:')
    articles = s.exec(select(NewsArticle)).all()
    print(len(articles))
    for a in articles[:10]:
        print(a.symbol, a.title[:50])
