import os
import logging

# --- LOGGING CONFIGURATION ---
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

# --- CORE SYSTEM SETTINGS ---
# For Aiven/Supabase, set this in your environment variables.
# Use sqlite for local testing if DATABASE_URL is not set.
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///finreview.db')

CORS_ALLOW_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ALLOW_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080').split(',') if origin.strip()]

TABLE_NAME = os.getenv('TABLE_NAME', 'FinReviewTable')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
DYNAMODB_ENDPOINT = os.getenv('DYNAMODB_ENDPOINT', None)

# --- MARKET DATA API (e.g., AlphaVantage, Polygon, Fyers) ---
MARKET_DATA_API_KEY = os.getenv('MARKET_DATA_API_KEY', 'YOUR_MARKET_API_KEY')
MARKET_DATA_BASE_URL = os.getenv('MARKET_DATA_BASE_URL', 'https://query1.finance.yahoo.com/v8/finance/chart/')
# generic default used only for legacy compatibility
PRICE_CACHE_MINUTES = int(os.getenv('PRICE_CACHE_MINUTES', 5))
# finer control: stocks refresh every 30 minutes, mutual funds twice a day
STOCK_PRICE_CACHE_MINUTES = int(os.getenv('STOCK_PRICE_CACHE_MINUTES', 30))
MF_PRICE_CACHE_MINUTES = int(os.getenv('MF_PRICE_CACHE_MINUTES', 12 * 60))

PROVIDER_RETRIES = int(os.getenv('PROVIDER_RETRIES', 3))
PROVIDER_TIMEOUT = int(os.getenv('PROVIDER_TIMEOUT', 10))

# --- AI INSIGHTS (OpenRouter.ai / OpenAI) ---
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
AI_MODEL_ENDPOINT = os.getenv('AI_MODEL_ENDPOINT', 'https://openrouter.ai/api/v1/chat/completions')
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'google/gemma-3-27b-it:free')
INSIGHTS_PER_DAY_LIMIT = int(os.getenv('INSIGHTS_PER_DAY_LIMIT', 3))

# --- NEWS INTELLIGENCE (Hybrid RSS + NewsData.io Backup) ---
RSS_FEEDS = [
    # MoneyControl - Highly reliable for corporate actions
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.moneycontrol.com/rss/business.xml",
    "https://www.moneycontrol.com/rss/results.xml",      # Targeted for RESULT category
    "https://www.moneycontrol.com/rss/marketoutlook.xml",
    
    # Economic Times - Broad market coverage
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    
    # LiveMint - Excellent for company-specific news
    "https://www.livemint.com/rss/companies",
    "https://www.livemint.com/rss/markets",
    
    # Business Standard & Financial Express - Deep corporate analysis
    "https://www.business-standard.com/rss/companies-101.rss",
    "https://www.financialexpress.com/market/feed/",
    
    # Official Exchanges (NSE Aggregator)
    "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml"
]
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
NEWS_API_BASE_URL = os.getenv('NEWS_API_BASE_URL', 'https://newsdata.io/api/1/news')
NEWS_DAILY_LIMIT = 200 # Credits
NEWS_BATCH_SIZE = 10 # Articles per credit

# --- MUTUAL FUND DATA API (mfapi.in) ---
MFAPI_BASE_URL = os.getenv('MFAPI_BASE_URL', 'https://api.mfapi.in/mf/')

# --- NOTIFICATIONS (Telegram / Email) ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')
SES_EMAIL_SENDER = os.getenv('SES_EMAIL_SENDER', 'notifications@finreview.com')

# --- INDEX SYMBOLS (configurable) ---
NIFTY50_SYMBOL = os.getenv('NIFTY50_SYMBOL', '^NSEI')
NIFTY_NEXT50_SYMBOL = os.getenv('NIFTY_NEXT50_SYMBOL', '^NSMIDCP')
# allow comma-separated alternate symbols to try if primary fails (e.g. remove caret)
NIFTY_NEXT50_FALLBACKS = [s for s in os.getenv('NIFTY_NEXT50_FALLBACKS', '').split(',') if s]

# --- ANALYTICS & LOGIC THRESHOLDS ---
TOLERANCE_BAND_PCT = float(os.getenv('TOLERANCE_BAND_PCT', 5.0))
CONCENTRATION_THRESHOLD_PCT = float(os.getenv('CONCENTRATION_THRESHOLD_PCT', 25.0))
QUIET_HOURS_START = int(os.getenv('QUIET_HOURS_START', 22)) # 10 PM
QUIET_HOURS_END = int(os.getenv('QUIET_HOURS_END', 8))      # 8 AM
IDEMPOTENCY_TTL_DAYS = int(os.getenv('IDEMPOTENCY_TTL_DAYS', 7))
