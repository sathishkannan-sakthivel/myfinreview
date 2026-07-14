import asyncio
import logging

from repositories.portable_repository import PortableInsightsRepository, PortableNewsRepository
from models.portable_models import Insight, InsightType
from config import settings
import json
import hashlib
import httpx
from datetime import datetime, timedelta
from sqlmodel import Session

logger = logging.getLogger(__name__)

class PortableInsightService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = PortableInsightsRepository(session)
        self.news_repo = PortableNewsRepository(session)
        self.limit = settings.INSIGHTS_PER_DAY_LIMIT

    async def generate_structured_insights(self, user_id: int, change_summary: dict, portfolio_data: dict) -> list:
        """
        Main entry point for generating AI intelligence (async version).
        """
        final_insights = []
        logger.debug(f"Starting insight generation for user {user_id}")

        try:
            # 1. Standard Change Explanations (Logic-based)
            events = change_summary.get('events', [])
            if events:
                candidates = self._map_signals_to_candidates(user_id, events)
                for candidate in candidates:
                    if not self._is_duplicate(user_id, candidate):
                        logger.debug("Calling LLM for change explanation...")
                        candidate['content'] = await self._call_llm_for_explanation(candidate)
                        final_insights.append(candidate)

            # 2. Daily Portfolio Briefing (Batching Strategy)
            holdings = portfolio_data.get('holdings', [])
            symbols = [h.get('symbol') for h in holdings if h.get('symbol')]
            
            if symbols:
                logger.debug(f"Fetching news for symbols: {symbols}")
                user_news = self.news_repo.get_latest_news_for_user(symbols, limit_per_symbol=5)
                
                briefing = await self.generate_portfolio_daily_briefing(user_id, symbols, user_news)
                if briefing:
                    final_insights.append(briefing)

            # 3. Save Top Insights
            final_insights.sort(key=lambda x: x.get('importance_score', 5.0), reverse=True)
            for insight in final_insights[:5]: # Max 5 total per day
                itype = insight['type']
                if hasattr(itype, 'value'): itype = itype.value
                
                self.repo.save_insight(
                    user_id=user_id, 
                    content=insight['content'], 
                    type=itype,
                    importance_score=insight.get('importance_score', 5.0), 
                    change_hash=insight.get('change_hash', 'batch_briefing')
                )
            
            return final_insights
        except Exception as e:
            logger.exception(f"CRITICAL ERROR in generate_structured_insights: {e}")
            return []

    async def generate_portfolio_daily_briefing(self, user_id: int, symbols: list, news_data: dict):
        all_headlines = []
        for symbol, articles in news_data.items():
            for a in articles:
                all_headlines.append(f"[{symbol}] {a.title}")

        if not all_headlines:
            logger.debug("No news found. Generating fallback summary.")
            prompt = (
                f"You are an impartial data educator reviewing these assets: {', '.join(symbols)}.\n"
                "No news headlines were available for the last 24 hours.\n"
                "Based solely on available data, write a 2-sentence factual summary of market sentiment."            )
        else:
            news_text = "\n".join(all_headlines[:30])
            prompt = (
                f"You are an impartial data educator reviewing these assets: {', '.join(symbols)}.\n"
                f"Recent news headlines:\n\n{news_text}\n\n"
                "Provide a 2-sentence factual summary highlighting the most significant signal without advice."
            )

        logger.debug("Calling async OpenRouter for Daily Briefing...")
        content = await self._call_openrouter_free(prompt)
        
        return {
            'user_id': user_id,
            'type': InsightType.PORTFOLIO_BRIEFING,
            'content': content,
            'importance_score': 8.5,
            'confidence_score': 0.85,
            'source_signals': ['NEWS_BATCH'],
            'change_hash': hashlib.md5((str(all_headlines) + str(datetime.now().timestamp())).encode()).hexdigest(),
            'explanation_data': {'news_count': len(all_headlines)}
        }

    async def _call_openrouter_free(self, prompt: str):
        if not settings.OPENROUTER_API_KEY:
            return (
                "AI summary unavailable in this environment because no LLM provider key is configured. "
                "The portfolio, transaction, allocation, and analytics data remain available for review."
            )
        # List of free models to try in order of preference
        models_to_try = [
            settings.AI_MODEL_NAME, # Usually 'openrouter/free'
            "google/gemma-3-27b-it:free",
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "openrouter/free"
        ]
        
        # Remove duplicates while preserving order
        models_to_try = list(dict.fromkeys(models_to_try))

        system_prompt = (
            "You are a 'Data Educator' for an Indian investment portfolio. "
            "Your goal is to explain data and market movements objectively. "
            "STRICT RULES: \n"
            "1. NEVER give advice to 'Buy', 'Sell', 'Hold', or 'Invest'.\n"
            "2. NEVER use the words 'Recommend' or 'Advise' regarding specific actions.\n"
            "3. FOCUS on facts: 'Your exposure to X is Y%', 'Sector Z moved by W%'.\n"
            "4. ALWAYS act as an informational diagnostic tool, not a financial advisor."
        )

        last_error = ""
        async with httpx.AsyncClient(timeout=30) as client:
            for model in models_to_try:
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
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
                    content = response.json()['choices'][0]['message']['content']
                    disclaimer = "\n\n---\n*Disclaimer: FinReview provides mathematical data analysis for educational purposes only. Not SEBI-registered.*"
                    return content + disclaimer
                except Exception as e:
                    logger.error(f"OpenRouter async error with {model}: {e}")
                    last_error = str(e)
                    continue

        return f"Unable to generate AI summary (Last Error: {last_error}). Please check the raw news feed."

    async def _call_llm_for_explanation(self, candidate: dict) -> str:
        return await self._call_openrouter_free(f"Provide a neutral explanation of this portfolio change: {candidate['explanation_data']}")

    def _map_signals_to_candidates(self, user_id: int, events: list):
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
                'change_hash': hashlib.md5((str(signals) + str(datetime.now().timestamp())).encode()).hexdigest(),
                'explanation_data': {'total_change_pct': events_by_type['VALUE'][0]['metadata'].get('change_pct', 0)}
            })
        return candidates

    def _is_duplicate(self, user_id: int, candidate: dict):
        """
        Check if an identical insight (same type and data hash) was recently generated.
        """
        latest = self.repo.get_latest_insight(user_id, candidate['type'].value if hasattr(candidate['type'], 'value') else candidate['type'])
        if latest and latest.change_hash == candidate['change_hash']:
            logger.debug(f"Skipping duplicate insight for type {candidate['type']}")
            return True
        return False
