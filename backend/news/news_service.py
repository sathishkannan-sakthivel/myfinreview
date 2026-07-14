import feedparser
import requests
import hashlib
import time
from bs4 import BeautifulSoup
from repositories.news_repository import NewsRepository
from repositories.dynamo_client import DynamoClient
from config import settings

class NewsService:
    def __init__(self):
        self.repo = NewsRepository()
        self.client = DynamoClient()
        self.rss_feeds = settings.RSS_FEEDS
        self.api_key = settings.NEWS_API_KEY
        self.api_base_url = settings.NEWS_API_BASE_URL

    def fetch_and_store_news(self, symbols: list):
        """
        Hybrid strategy: 
        1. Ingest from free RSS feeds (Primary)
        2. Use NewsData.io for targeted gaps (Backup/Secondary)
        """
        if not symbols:
            return False

        # 1. Fetch from RSS (Zero Cost)
        rss_articles = self._fetch_from_rss(symbols)
        
        # 2. If RSS found very little, use backup API (Cost-aware)
        api_articles = []
        if len(rss_articles) < 5:
            print("RSS yield low, triggering NewsData.io backup...")
            api_articles = self._fetch_from_news_api_backup(symbols)

        all_news = rss_articles + api_articles
        
        # 3. Deduplicate and Save
        stored_count = 0
        for item in all_news:
            if self._is_new_story(item['title']):
                for symbol in item['matched_symbols']:
                    self.repo.save_news_item(symbol, item['title'], item['link'], "NEUTRAL")
                self._mark_story_as_seen(item['title'])
                stored_count += 1
                
        return stored_count > 0

    def _fetch_from_rss(self, symbols: list):
        matched_articles = []
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    # Basic keyword matching
                    content = (entry.title + " " + entry.get('summary', '')).upper()
                    matches = [s for s in symbols if str(s).upper() in content]
                    
                    if matches:
                        matched_articles.append({
                            'title': entry.title,
                            'link': entry.link,
                            'matched_symbols': matches,
                            'source': 'RSS'
                        })
            except Exception as e:
                print(f"RSS Fetch Error ({feed_url}): {e}")
        return matched_articles

    def _fetch_from_news_api_backup(self, symbols: list):
        """
        NewsData.io implementation (Backup)
        Utilizes country=in and queries for symbols.
        """
        if not self.api_key or self.api_key == 'YOUR_NEWSDATA_IO_KEY':
            return []

        articles = []
        # Join symbols for a broad query or pick top 3 to save credits
        query = " OR ".join(symbols[:3]) 
        
        try:
            params = {
                'apikey': self.api_key,
                'q': query,
                'country': 'in',
                'language': 'en',
                'category': 'business,technology'
            }
            response = requests.get(self.api_base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for result in data.get('results', []):
                    # Cross-reference which symbol this article belongs to
                    content = (result.get('title', '') + " " + result.get('description', '')).upper()
                    matches = [s for s in symbols if str(s).upper() in content]
                    
                    if matches:
                        articles.append({
                            'title': result['title'],
                            'link': result['link'],
                            'matched_symbols': matches,
                            'source': 'NewsData.io'
                        })
        except Exception as e:
            print(f"NewsData API Error: {e}")
            
        return articles

    def _is_new_story(self, title: str):
        title_hash = hashlib.md5(title.encode()).hexdigest()
        existing = self.client.get_item(f'NEWSHASH#{title_hash}', 'SEEN')
        return existing is None

    def _mark_story_as_seen(self, title: str):
        title_hash = hashlib.md5(title.encode()).hexdigest()
        self.client.put_item({
            'PK': f'NEWSHASH#{title_hash}',
            'SK': 'SEEN',
            'timestamp': datetime.utcnow().isoformat()
        })

    def get_user_news(self, symbols: list):
        return self.repo.get_latest_news_for_user(symbols)

from datetime import datetime
