import os
import requests
import feedparser
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def safe_get(url, params=None, timeout=15):
    try:
        r = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "kalshi-q-series-bot/1.0"}
        )
        if r.status_code != 200:
            return None
        return r
    except Exception:
        return None


def search_google_news(query, limit=5):
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)

    results = []

    for entry in feed.entries[:limit]:
        results.append({
            "source": "Google News RSS",
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
        })

    return results


def search_gdelt_news(query, limit=5):
    url = "https://api.gdeltproject.org/api/v2/doc/doc"

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": limit,
        "sort": "HybridRel",
    }

    r = safe_get(url, params=params)

    if not r:
        return []

    try:
        data = r.json()
    except Exception:
        return []

    articles = data.get("articles", [])
    results = []

    for item in articles[:limit]:
        results.append({
            "source": "GDELT News",
            "title": item.get("title", ""),
            "link": item.get("url", ""),
            "summary": item.get("seendate", ""),
        })

    return results


def search_reddit(query, limit=5):
    url = "https://www.reddit.com/search.json"

    params = {
        "q": query,
        "sort": "new",
        "limit": limit,
    }

    r = safe_get(url, params=params)

    if not r:
        return []

    try:
        data = r.json()
    except Exception:
        return []

    posts = data.get("data", {}).get("children", [])
    results = []

    for post in posts[:limit]:
        d = post.get("data", {})
        results.append({
            "source": "Reddit",
            "title": d.get("title", ""),
            "link": "https://reddit.com" + d.get("permalink", ""),
            "summary": d.get("selftext", "")[:300],
            "subreddit": d.get("subreddit", ""),
            "score": d.get("score", 0),
            "comments": d.get("num_comments", 0),
        })

    return results


def search_x(query, limit=5):
    x_token = os.getenv("X_BEARER_TOKEN")

    if not x_token:
        return [{
            "source": "X/Twitter",
            "title": "X search disabled",
            "link": "",
            "summary": "Add X_BEARER_TOKEN to .env to enable official X search.",
        }]

    return [{
        "source": "X/Twitter",
        "title": "X API placeholder",
        "link": "",
        "summary": "X API key detected, but endpoint wiring comes next.",
    }]


def broad_research(query):
    results = []

    results.extend(search_google_news(query, limit=5))
    results.extend(search_gdelt_news(query, limit=5))
    results.extend(search_reddit(query, limit=5))
    results.extend(search_x(query, limit=5))

    return results


def print_research(query):
    print("\nBROAD SOURCE RESEARCH")
    print(f"Query: {query}")
    print("-" * 60)

    results = broad_research(query)

    if not results:
        print("No outside source results found.")
        return

    for i, item in enumerate(results, start=1):
        print("-" * 60)
        print(f"#{i}")
        print(f"Source: {item.get('source')}")
        if item.get("subreddit"):
            print(f"Subreddit: r/{item.get('subreddit')}")
        print(f"Title: {item.get('title')}")
        if item.get("score") is not None and item.get("source") == "Reddit":
            print(f"Reddit Score: {item.get('score')} | Comments: {item.get('comments')}")
        print(f"Link: {item.get('link')}")
        summary = item.get("summary") or ""
        if summary:
            print(f"Summary: {summary[:300]}")


if __name__ == "__main__":
    query = input("Search query: ").strip()
    print_research(query)