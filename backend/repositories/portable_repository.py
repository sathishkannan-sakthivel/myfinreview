from sqlmodel import Session, select
from models.portable_models import Insight, InsightType, NewsArticle, Holding, Transaction
from datetime import datetime

class PortableInsightsRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_insight(self, user_id: int, content: str, type: str, **kwargs):
        insight = Insight(
            user_id=user_id,
            content=content,
            type=InsightType(type),
            importance_score=kwargs.get('importance_score', 5.0),
            change_hash=kwargs.get('change_hash', 'batch_briefing'),
            timestamp=datetime.utcnow()
        )
        self.session.add(insight)
        self.session.commit()
        self.session.refresh(insight)
        return insight

    def get_latest_insight(self, user_id: int, type: str):
        statement = select(Insight).where(
            Insight.user_id == user_id, 
            Insight.type == InsightType(type)
        ).order_by(Insight.timestamp.desc())
        return self.session.exec(statement).first()

    def get_insights_history(self, user_id: int, type: str, limit: int = 10):
        statement = select(Insight).where(
            Insight.user_id == user_id, 
            Insight.type == InsightType(type)
        ).order_by(Insight.timestamp.desc()).limit(limit)
        return self.session.exec(statement).all()

class PortableHoldingRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_user_holdings(self, user_id: int):
        statement = select(Holding).where(Holding.user_id == user_id)
        return self.session.exec(statement).all()

    def get_holding(self, user_id: int, symbol: str):
        statement = select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        return self.session.exec(statement).first()

    def save_holding(self, holding: 'Holding'):
        self.session.add(holding)
        self.session.commit()
        self.session.refresh(holding)
        return holding

class PortableTransactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def record_transaction(self, transaction: 'Transaction'):
        # 1. Check if hash exists for upsert
        if transaction.hash:
            statement = select(Transaction).where(Transaction.hash == transaction.hash)
            existing = self.session.exec(statement).first()
            if existing:
                print(f"DEBUG: Transaction with hash {transaction.hash} already exists. Skipping.")
                return existing

        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def get_transactions(self, user_id: int, symbol: str = None):
        statement = select(Transaction).where(Transaction.user_id == user_id)
        if symbol:
            statement = statement.where(Transaction.symbol == symbol)
        statement = statement.order_by(Transaction.date.desc())
        return self.session.exec(statement).all()

class PortableNewsRepository:
    _analyzer = None

    def __init__(self, session: Session):
        self.session = session
        # Lazy-load analyzer once
        if PortableNewsRepository._analyzer is None:
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                PortableNewsRepository._analyzer = SentimentIntensityAnalyzer()
            except ImportError:
                PortableNewsRepository._analyzer = "lexicon"

    def save_news_item(self, symbol: str, title: str, link: str, sentiment: str = "NEUTRAL", summary: str = None, published_at: str = None, commit: bool = True, category: str = "NEWS"):
        # published_at may come as string; attempt parse if provided
        pub_dt = datetime.utcnow()
        if published_at:
            try:
                pub_dt = datetime.fromisoformat(published_at)
            except Exception:
                try:
                    pub_dt = datetime.strptime(published_at, '%a, %d %b %Y %H:%M:%S %Z')
                except Exception:
                    pass
        
        text_for_sentiment = (summary or title or "")
        sentiment_score = 0.0
        
        if self._analyzer == "lexicon":
            # fallback lexicon
            pos_words = {"gain", "gains", "rise", "rises", "up", "beat", "beats", "profit", "profits", "surge", "surges", "growth", "upgrade", "upgraded", "outperform", "outperforms", "strong", "bull", "positive", "record", "improve", "improved", "win", "wins", "benefit", "boost", "favourable", "favorable", "rebound", "recover", "recovery", "soar", "soars", "better"}
            neg_words = {"loss", "losses", "fall", "falls", "down", "drop", "drops", "decline", "declines", "weak", "weakness", "cut", "cuts", "sell", "selling", "warning", "warn", "warns", "negative", "fine", "fines", "fraud", "frauds", "bear", "miss", "missed", "plunge", "slowdown", "lawsuit", "probe", "investigation", "concern", "pressure", "debt", "default", "selloff", "penalty"}
            pos = 0
            neg = 0
            words = [w.strip(".,!?:;()\"'\n\r").lower() for w in text_for_sentiment.split()]
            for w in words:
                if w in pos_words: pos += 1
                if w in neg_words: neg += 1
            if (pos + neg) > 0:
                sentiment_score = (pos - neg) / (pos + neg)
        elif self._analyzer:
            try:
                sentiment_score = self._analyzer.polarity_scores(text_for_sentiment).get('compound', 0.0)
            except:
                pass

        news = NewsArticle(
            symbol=symbol,
            title=title,
            link=link,
            summary=summary,
            category=category,
            sentiment=round(float(sentiment_score), 2),
            published_at=pub_dt
        )
        self.session.add(news)
        if commit:
            self.session.commit()
            self.session.refresh(news)
        return news

    def get_latest_news_for_user(self, symbols: list, limit_per_symbol: int = 5):
        # In SQL, we can do this more efficiently, but for parity, we'll return a dict
        results = {}
        for symbol in symbols:
            statement = select(NewsArticle).where(
                NewsArticle.symbol == symbol
            ).order_by(NewsArticle.published_at.desc()).limit(limit_per_symbol)
            results[symbol] = self.session.exec(statement).all()
        return results
