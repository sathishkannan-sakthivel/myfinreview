PriceCache refresher scheduling
================================

Overview
--------
This repository includes `pricecache_refresher.py` which scans the `PriceCache` table and refreshes stale LTPs using existing providers.

Recommended approach
--------------------
- Use an external scheduler (cron / Task Scheduler) in production. It's resilient and independent of the web server.
- Two recommended scheduled jobs:
  - Stocks: run every 30 minutes (or every 15 minutes if you want aggressive freshness).
  - Mutual funds: run twice daily (e.g., 06:00 and 18:00).

Examples
--------

1) Cron (Linux/macOS)

Run stocks every 30 minutes:

```bash
*/30 * * * * cd /path/to/FinReview/backend && /usr/bin/python3 pricecache_refresher.py
```

Run mutual funds twice daily at 06:00 and 18:00:

```bash
0 6,18 * * * cd /path/to/FinReview/backend && /usr/bin/python3 pricecache_refresher.py
```

If you prefer separate commands (stocks-only / mfs-only), add the flags `--stocks-only` or `--mfs-only` accordingly.

2) systemd unit + timers (Linux)

Create `/etc/systemd/system/pricecache-refresher.service`:

```
[Unit]
Description=PriceCache refresher

[Service]
Type=oneshot
WorkingDirectory=/path/to/FinReview/backend
ExecStart=/usr/bin/python3 pricecache_refresher.py
```

Create `/etc/systemd/system/pricecache-refresher.timer` to run every 30 minutes:

```
[Unit]
Description=Run PriceCache refresher every 30 minutes

[Timer]
OnCalendar=*:0/30
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pricecache-refresher.timer
```

3) Windows Task Scheduler (example)

- Create a Basic Task, name it `PriceCache Refresher`.
- Action: `Start a program`.
- Program/script: `C:\Path\To\Python\python.exe`
- Add arguments: `pricecache_refresher.py`
- Start in: `D:\Exstream Happenings\Hackathon\Sparkathon\Project\FinReview\backend`
- Trigger: set to Daily and repeat every 30 minutes for stocks, and create a second task for mutual funds at specific times.

Dry-run
-------
Use `--dry-run` to list stale symbols without making network calls:

```bash
python pricecache_refresher.py --dry-run
```

Notes
-----
- The script uses `STOCK_REFRESH_MINUTES` and `MF_REFRESH_MINUTES` from `config.settings` if present; defaults are 30 minutes for stocks and 12 hours for MFs.
- For production, schedule at least as frequently as the smallest refresh window you want to enforce.
