# FinReview Background Scheduling

To maintain peak performance and avoid UI delays, certain diagnostic tasks are decoupled from the user dashboard and run as background processes.

## 1. Price Cache Refresher
Keeps portfolio valuations up to date by fetching the latest market prices (LTP).

*   **Script:** `backend/utils/pricecache_refresher.py`
*   **Recommended Schedule:** 
    *   Stocks: Every 15-30 minutes during market hours.
    *   Mutual Funds: Twice daily (e.g., 9 AM and 9 PM).

## 2. News Refresher
Synchronizes market news for all symbols held in user portfolios and alert watchlists.

*   **Script:** `backend/utils/news_refresher.py`
*   **Recommended Schedule:** Every 30-60 minutes.

---

## How to Schedule (Windows)

1. Open **Task Scheduler**.
2. Create a new "Basic Task" for each refresher.
3. **Program/script:** `C:\Path\To\Python\python.exe`
4. **Add arguments:** `utils/news_refresher.py` (or `pricecache_refresher.py`)
5. **Start in:** `D:\Exstream Happenings\Hackathon\Sparkathon\Project\FinReview\backend`

## How to Schedule (Linux/Cron)

```bash
# Refresh prices every 30 minutes
*/30 * * * * cd /path/to/FinReview/backend && python3 utils/pricecache_refresher.py

# Refresh news every hour
0 * * * * cd /path/to/FinReview/backend && python3 utils/news_refresher.py
```
