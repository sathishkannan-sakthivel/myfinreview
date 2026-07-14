"""Load the sample portfolio for an existing FinReview user.

Usage:
    cd backend
    python ../scripts/seed_sample_portfolio.py --user-id 1
"""

import argparse
import asyncio
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, ROOT)

from database import get_session, init_db  # noqa: E402
from main import load_sample_portfolio_for_user  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    args = parser.parse_args()

    init_db()
    session_gen = get_session()
    session = next(session_gen)
    try:
        await load_sample_portfolio_for_user(args.user_id, session)
        print(f"Sample portfolio loaded for user {args.user_id}.")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())