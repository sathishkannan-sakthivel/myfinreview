import os, sys
sys.path.append(os.getcwd())
from sqlmodel import Session, select
from database import engine
from models.portable_models import NewsArticle

if __name__ == '__main__':
    confirm = input("This will DELETE ALL rows from NewsArticle. Type YES to continue: ")
    if confirm.strip().upper() != 'YES':
        print('Aborting.')
        sys.exit(0)
    with Session(engine) as session:
        statement = select(NewsArticle)
        rows = session.exec(statement).all()
        count = len(rows)
        for r in rows:
            session.delete(r)
        session.commit()
    print(f"Truncated NewsArticle table; removed {count} rows")
