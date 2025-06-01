# news_fetcher.py
import requests
from newspaper import Article, ArticleException, Config as NewspaperConfig
import config
import os

def get_top_trending_headlines_from_newsapi():
    if not config.NEWS_API_KEY or config.NEWS_API_KEY.startswith("YOUR_"):
        print("ERROR: NewsAPI key not configured in config.py."); return None
    base_url = "https://newsapi.org/v2/top-headlines?"; params = {
        "language": "en", "pageSize": config.NEWS_NUM_ARTICLES_TO_CONSIDER * 2,
        "apiKey": config.NEWS_API_KEY}
    if config.NEWS_COUNTRY: params["country"] = config.NEWS_COUNTRY
    if config.NEWS_CATEGORY: params["category"] = config.NEWS_CATEGORY
    if not config.NEWS_COUNTRY and not config.NEWS_CATEGORY:
        print("WARN: NewsAPI needs country or category for top-headlines. Defaulting to country='us'.")
        params["country"] = "us"
    api_url = base_url + "&".join([f"{k}={v}" for k,v in params.items()])
    try:
        print(f"Fetching headlines from NewsAPI (timeout: {config.NETWORK_TIMEOUT_SECONDS}s)...")
        r = requests.get(api_url, timeout=config.NETWORK_TIMEOUT_SECONDS); r.raise_for_status(); data = r.json()
        if data.get('status') == 'ok' and data.get('articles'):
            h = [{"url":a['url'],"title":a['title']} for a in data['articles'] if a.get('url')and a.get('title')and 'http'in a['url']and len(a['title'])>10]
            if h: print(f"Fetched {len(h)} headlines."); return h
            print("No suitable headlines from NewsAPI."); return None
        else: print(f"NewsAPI Error: {data.get('message','Unknown')}"); return None
    except requests.exceptions.Timeout: print(f"NewsAPI request timed out."); return None
    except requests.exceptions.RequestException as e: print(f"NewsAPI request exception: {e}"); return None
    except Exception as e: print(f"Unexpected error fetching headlines: {e}"); return None

def extract_article_content(article_url, article_title_hint=""):
    if not article_url: return None
    try:
        np_conf = NewspaperConfig(); np_conf.request_timeout=config.NETWORK_TIMEOUT_SECONDS
        np_conf.fetch_images=False; np_conf.memoize_articles=False
        article = Article(article_url, config=np_conf)
        print(f"  Downloading/parsing: '{article_title_hint or article_url}'...")
        article.download(); article.parse()
        if not article.is_parsed or not article.text or len(article.text) < 250:
            print(f"    Extraction failed for '{article_title_hint or article_url}'. Reason: {'not parsed' if not article.is_parsed else 'text too short'} (Len: {len(article.text or '')}).")
            return None
        title = article.title or article_title_hint
        print(f"    Successfully extracted: '{title}'")
        return {"title":title,"text":article.text,"url":article_url,"summary":article.summary,"keywords":article.keywords}
    except Exception as e: print(f"    Exception extracting '{article_title_hint or article_url}': {e}"); return None