from typing import List, Dict, Any
from ..models import ChangeEvent, ChangeType

class NewsImpactDetector:
    def detect(self, new_news: Dict[str, List[Dict[str, Any]]]) -> List[ChangeEvent]:
        events = []
        for symbol, articles in new_news.items():
            for article in articles:
                sentiment = article.get('sentiment', 'NEUTRAL')
                impact = 4.0 if sentiment != 'NEUTRAL' else 1.0
                
                events.append(ChangeEvent(
                    type=ChangeType.NEWS,
                    description=f"New news for {symbol}: {article.get('title')}",
                    impact_score=impact,
                    metadata={"symbol": symbol, "title": article.get('title'), "sentiment": sentiment}
                ))
        return events
