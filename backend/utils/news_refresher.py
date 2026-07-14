import sys
import os
from pathlib import Path

# Add backend directory to sys.path so we can import local modules
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

import asyncio
import logging
from datetime import datetime
from sqlmodel import select, Session
from database import engine
from models.portable_models import Holding, AlertRule
from news.portable_news_service import PortableNewsService

logger = logging.getLogger("news_refresher")
logging.basicConfig(level=logging.INFO)

async def refresh_all_news():
    """
    Background task to ingest news for all active symbols across all users.
    Optimized to minimize DB connection hold time.
    """
    now = datetime.now()
    logger.info(f"Starting news refresh at {now.isoformat()}")
    
    all_symbols = []
    
    # 1. SHORT DB HIT: Collect symbols and close session immediately
    with Session(engine) as session:
        holding_symbols = session.exec(select(Holding.symbol)).all()
        rule_symbols = session.exec(select(AlertRule.symbol)).all()
        all_symbols = list(set(s for s in (holding_symbols + rule_symbols) if s))
        
    if not all_symbols:
        logger.info("No active symbols found to refresh news for.")
        return

    logger.info(f"Found {len(all_symbols)} unique symbols. Starting parallel network fetch...")
    
    # 2. HEAVY NETWORK I/O (Async, No DB session held)
    # Create a dummy session for the service (it will be used later for save)
    with Session(engine) as save_session:
        service = PortableNewsService(save_session)
        try:
            # This call now handles its own async network parallelization
            count = await service.fetch_and_store_news(all_symbols)
            logger.info(f"News refresh complete. Ingested {count} new stories.")
        except Exception as e:
            logger.error(f"Error during news ingestion: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="News Refresher: background ingestion for all active symbols")
    args = parser.parse_args()

    async def runner():
        await refresh_all_news()

    # News ingestion is predominantly I/O bound (RSS/APIs)
    # The optimized service uses asyncio for providers
    asyncio.run(runner())

if __name__ == "__main__":
    main()
