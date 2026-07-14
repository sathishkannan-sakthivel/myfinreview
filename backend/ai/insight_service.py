import asyncio
import logging

from repositories.insights_repository import InsightsRepository
from repositories.news_repository import NewsRepository
from .models import Insight, InsightType
from config import settings
import json
import hashlib
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InsightService:
    def __init__(self):
        self.repo = InsightsRepository()
        self.news_repo = NewsRepository()
        self.limit = settings.INSIGHTS_PER_DAY_LIMIT

    async def generate_structured_insights(self, user_id, change_summary, portfolio_data) -> list:
        """
        Main entry point for generating AI intelligence.
        Uses async HTTP calls and batching logic. Returns a list of insight dicts.
        """
        final_insights = []

        # 1. Standard Change Explanations (Logic-based)
        events = change_summary.get('events', [])
        if events:
            candidates = self._map_signals_to_candidates(user_id, events)
            for candidate in candidates:
                if not self._is_duplicate(user_id, candidate):
                    candidate['content'] = await self._call_llm_for_explanation(candidate)
                    final_insights.append(candidate)

        # 2. Daily Portfolio Briefing (Batching Strategy)
        symbols = [h['symbol'] for h in portfolio_data.get('holdings', [])]
        user_news = self.news_repo.get_latest_news_for_user(symbols, limit_per_symbol=5)
        
        briefing = await await self.generate_portfolio_daily_briefing(user_id, symbols, user_news)
        if briefing:
            final_insights.append(briefing)

        # 3. Save Top Insights
        final_insights.sort(key=lambda x: x.get('importance_score', 5.0), reverse=True)
        for insight in final_insights[:5]: # Max 5 total per day
            self.repo.save_insight(
                user_id=user_id, 
                content=insight['content'], 
                type=insight['type'].value if isinstance(insight['type'], InsightType) else insight['type'],
                importance_score=insight.get('importance_score', 5.0), 
                confidence_score=insight.get('confidence_score', 0.9),
                source_signals=insight.get('source_signals', []), 
                explanation_data=insight.get('explanation_data', {}),
                change_hash=insight.get('change_hash', 'batch_briefing')
            )
        
        return final_insights

    async def generate_portfolio_daily_briefing(self, user_id, symbols, news_data):
        """
        2026 Batching Strategy:
        Collects all news and generates a single 'So What' summary 
        using OpenRouter's free tier. Persona changed to Data Educator (non-advisory).
        """
        # Flatten news for prompt
        all_headlines = []
        for symbol, articles in news_data.items():
            for a in articles:
                all_headlines.append(f"[{symbol}] {a['title']}")

        if not all_headlines:
            return None

        # Build Prompt (Data Educator persona to avoid advisory language)
        news_text = "\n".join(all_headlines[:30])
        prompt = (
            f"You are an impartial data educator reviewing the following Indian portfolio assets: {', '.join(symbols)}.\n"
            f"Here are recent news headlines associated with these symbols:\n\n{news_text}\n\n"
            "Task: Based solely on the data, write a 2-sentence factual summary highlighting the most significant risk or opportunity. "
            "Do NOT provide investment advice or suggest trades; strictly describe the data."
        )

        content = await self._call_openrouter_free(prompt)
        
        return {
            'user_id': user_id,
            'type': InsightType.PORTFOLIO_BRIEFING,
            'content': content,
            'importance_score': 8.5,
            'confidence_score': 0.85,
            'source_signals': ['NEWS_BATCH'],
            'change_hash': hashlib.md5(news_text.encode()).hexdigest(),
            'explanation_data': {'news_count': len(all_headlines)}
        }

    async def _call_openrouter_free(self, prompt: str) -> str:
        if settings.OPENROUTER_API_KEY.startswith('YOUR_'):
            return "AI Summary: Market momentum is positive for your top holdings today."

        models_to_try = [
            settings.AI_MODEL_NAME,
            "google/gemma-3-27b-it:free",
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "openrouter/free"
        ]
        models_to_try = list(dict.fromkeys(models_to_try))

        last_error = ""
        async with httpx.AsyncClient(timeout=20) as client:
            for model in models_to_try:
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are an impartial data educator analyzing portfolio data without giving advice."},
                            {"role": "user", "content": prompt}
                        ]
                    }
                    headers = {
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://finreview.ai",
                        "X-Title": "FinReview"
                    }
                    
                    logger.debug(f"Sending async request to OpenRouter ({model})...")
                    response = await client.post(settings.AI_MODEL_ENDPOINT, json=payload, headers=headers)
                    if response.status_code == 404:
                        logger.debug(f"Model {model} not found (404). Trying next fallback...")
                        continue
                    elif response.status_code != 200:
                        logger.warning(f"OpenRouter Error Detail for {model}: {response.text}")
                        continue

                    response.raise_for_status()
                    return response.json()['choices'][0]['message']['content']
                except Exception as e:
                    logger.error(f"OpenRouter async error with {model}: {e}")
                    last_error = str(e)
                    continue

        return f"Unable to generate AI summary (Last Error: {last_error}). Please check the raw news feed."

    async def _call_llm_for_explanation(self, candidate) -> str:
        # Fallback to same free engine but with non-advisory persona
        return await self._call_openrouter_free(f"Provide a neutral explanation of this portfolio change: {candidate['explanation_data']}")

    def _map_signals_to_candidates(self, user_id, events):
        candidates = []
        events_by_type = {}
        for e in events:
            etype = e.get('type')
            events_by_type.setdefault(etype, []).append(e)
            
        if 'VALUE' in events_by_type:
            signals = [str(e.get('type')) for e in events]
            candidates.append({
                'user_id': user_id, 
                'type': InsightType.CHANGE_EXPLANATION, 
                'importance_score': 5.0,
                'confidence_score': 0.9, 
                'source_signals': signals, 
                'change_hash': hashlib.md5(str(signals).encode()).hexdigest(),
                'explanation_data': {'total_change_pct': events_by_type['VALUE'][0]['metadata'].get('change_pct', 0)}
            })
        return candidates

    def _is_duplicate(self, user_id, candidate):
        latest = self.repo.get_latest_insight(user_id, candidate['type'].value)
        return latest and latest.get('change_hash') == candidate['change_hash']

    def get_latest_insights(self, user_id):
        results = {}
        # Get one of each type
        for itype in InsightType:
            latest = self.repo.get_latest_insight(user_id, itype.value)
            if latest:
                results[itype.value] = {
                    "content": latest.get('content'),
                    "timestamp": latest.get('timestamp')
                }
        return results
