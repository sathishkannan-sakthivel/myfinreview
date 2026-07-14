import os, sys
sys.path.append(os.getcwd())
from sqlmodel import Session, select
from database import engine
from models.portable_models import NewsArticle

POS = {"gain", "gains", "rise", "rises", "up", "beat", "beats", "profit", "profits", "surge", "surges", "growth", "upgrade", "upgraded", "outperform", "outperforms", "strong", "bull", "positive", "record", "improve", "improved", "win", "wins", "benefit", "boost", "favourable", "favorable", "rebound", "recover", "recovery", "soar", "soars", "better"}
NEG = {"loss", "losses", "fall", "falls", "down", "drop", "drops", "decline", "declines", "weak", "weakness", "cut", "cuts", "sell", "selling", "warning", "warn", "warns", "negative", "fine", "fines", "fraud", "frauds", "bear", "miss", "missed", "plunge", "slowdown", "lawsuit", "probe", "investigation", "concern", "pressure", "debt", "default", "selloff", "penalty"}


def compute_sentiment(text: str) -> float:
    if not text:
        return 0.0
    # Prefer VADER if available
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        return round(analyzer.polarity_scores(text).get('compound', 0.0), 2)
    except Exception:
        t = text.lower()
        words = [w.strip(".,!?:;()\"'\n\r").lower() for w in t.split()]
        pos = sum(1 for w in words if w in POS)
        neg = sum(1 for w in words if w in NEG)
        if (pos + neg) == 0:
            return 0.0
        return round((pos - neg) / (pos + neg), 2)


if __name__ == '__main__':
    with Session(engine) as session:
        statement = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(200)
        rows = session.exec(statement).all()
        updated = 0
        for r in rows:
            text = (r.summary or r.title or "")
            s = compute_sentiment(text)
            if s != r.sentiment:
                r.sentiment = s
                session.add(r)
                updated += 1
        session.commit()
        print(f"Updated sentiment for {updated} articles")
