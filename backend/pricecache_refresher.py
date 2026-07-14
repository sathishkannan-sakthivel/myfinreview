import asyncio
import logging
from datetime import datetime, timedelta

from sqlmodel import select, Session

from database import engine
from models.portable_models import PriceCache
from services.portable_price_service import PortablePriceService
from config import settings

logger = logging.getLogger("pricecache_refresher")
logging.basicConfig(level=logging.INFO)


async def refresh_prices_once(dry_run: bool = False):
    """Fetch fresh LTPs for stale entries in PriceCache.

    - Stocks: refreshed if older than `stock_refresh_minutes` (default 30)
    - Mutual funds: refreshed if older than `mf_refresh_minutes` (default 12h)
    """
    stock_threshold = getattr(settings, "STOCK_REFRESH_MINUTES", 30)
    mf_threshold = getattr(settings, "MF_REFRESH_MINUTES", 12 * 60)

    now = datetime.now()
    with Session(engine) as session:
        statement = select(PriceCache)
        rows = session.exec(statement).all()
        if not rows:
            logger.info("No entries in PriceCache table.")
            return

        stocks_to_refresh = []
        mfs_to_refresh = []

        for r in rows:
            age_min = (now - r.timestamp).total_seconds() / 60.0
            if str(r.symbol).isdigit():
                if age_min >= mf_threshold:
                    mfs_to_refresh.append(r.symbol)
            else:
                if age_min >= stock_threshold:
                    stocks_to_refresh.append(r.symbol)

        # nothing to do
        if not stocks_to_refresh and not mfs_to_refresh:
            logger.info("No stale symbols to refresh (stocks=%d, mfs=%d).", len(stocks_to_refresh), len(mfs_to_refresh))
            return

        pps = PortablePriceService(session)

        # Use the bulk async fetch (we pass refresh_stale=True because the refresher's job is to update)
        async def fetch_group(symbols):
            if not symbols:
                return {}
            try:
                return await pps.get_prices_for_symbols(symbols, refresh_stale=True)
            except Exception as e:
                logger.exception("Error fetching prices for group: %s", e)
                return {}

        # nothing to do on dry-run
        if dry_run:
            logger.info("Dry run - would refresh stocks=%s mfs=%s", stocks_to_refresh, mfs_to_refresh)
            return

        # Run stocks and MFs concurrently
        tasks = [fetch_group(stocks_to_refresh), fetch_group(mfs_to_refresh)]
        results = await asyncio.gather(*tasks)

        updated = 0
        for group in results:
            for sym, price in group.items():
                if price is not None:
                    updated += 1

        logger.info("Refreshed %d symbols (stocks=%d, mfs=%d)", updated, len(stocks_to_refresh), len(mfs_to_refresh))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="PriceCache refresher: refresh LTPs for stale symbols")
    parser.add_argument("--dry-run", action="store_true", help="Identify stale symbols without performing network calls")
    parser.add_argument("--stocks-only", action="store_true", help="Refresh only stock tickers (non-numeric symbols)")
    parser.add_argument("--mfs-only", action="store_true", help="Refresh only mutual fund scheme codes (numeric symbols)")
    args = parser.parse_args()

    # Validate flags
    if args.stocks_only and args.mfs_only:
        raise SystemExit("Cannot use --stocks-only and --mfs-only together")

    async def runner():
        # If user requested a filtered run, pass that intent via kwargs
        await refresh_prices_once(dry_run=args.dry_run)

    asyncio.run(runner())


if __name__ == "__main__":
    main()
