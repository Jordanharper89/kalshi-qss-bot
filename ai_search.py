import re
import requests
import feedparser
from urllib.parse import quote_plus
from datetime import datetime, timezone


MAX_RESULTS_PER_SOURCE = 4
MAX_FINAL_RESULTS = 20


TRUSTED_DOMAINS = [
    "apnews.com",
    "reuters.com",
    "cnbc.com",
    "yahoo.com",
    "espn.com",
    "foxsports.com",
    "mlb.com",
    "nba.com",
    "nfl.com",
    "nhl.com",
    "weather.gov",
    "noaa.gov",
    "coingecko.com",
    "coinbase.com",
    "marketwatch.com",
    "billboard.com",
    "spotify.com",
    "variety.com",
    "hollywoodreporter.com",
    "whitehouse.gov",
    "realclearpolitics.com",
    "fivethirtyeight.com",
    "bbc.com",
    "cnn.com",
    "foxnews.com",
]


def safe_get(url, params=None, timeout=15):
    try:
        r = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": "kalshi-q-series-ai-search/1.0"},
        )
        if r.status_code != 200:
            return None
        return r
    except Exception:
        return None


def clean_html(text):
    text = str(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_category(query):
    q = query.lower()

    if any(x in q for x in ["btc", "bitcoin", "eth", "ethereum", "sol", "solana", "crypto"]):
        return "crypto"

    if any(x in q for x in ["mlb", "nba", "nfl", "nhl", "lineup", "injury", "pitcher", "game", "score"]):
        return "sports"

    if any(x in q for x in ["weather", "temperature", "temp", "rain", "wind", "storm", "snow"]):
        return "weather"

    if any(x in q for x in ["trump", "biden", "election", "poll", "approval", "speech", "white house"]):
        return "politics"

    if any(x in q for x in ["tesla", "spacex", "starship", "launch", "delivery"]):
        return "tesla_spacex"

    if any(x in q for x in ["song", "album", "movie", "box office", "billboard", "spotify"]):
        return "entertainment"

    if any(x in q for x in ["stock", "market", "earnings", "shares", "nasdaq", "s&p"]):
        return "stocks"

    return "general"


def build_queries(query):
    category = detect_category(query)
    q = query.strip()

    if category == "crypto":
        return [
            q,
            f"{q} live price movement",
            f"{q} latest crypto market news",
            f"{q} reddit",
            f"{q} Coinbase Binance CoinGecko",
        ]

    if category == "sports":
        return [
            q,
            f"{q} latest injury lineup news",
            f"{q} ESPN",
            f"{q} official team news",
            f"{q} odds movement",
        ]

    if category == "weather":
        return [
            q,
            f"{q} weather.gov forecast",
            f"{q} NOAA forecast",
            f"{q} hourly forecast update",
            f"{q} temperature wind update",
        ]

    if category == "politics":
        return [
            q,
            f"{q} today schedule",
            f"{q} public remarks today",
            f"{q} live updates",
            f"{q} White House schedule",
            f"{q} AP Reuters",
        ]

    if category == "tesla_spacex":
        return [
            q,
            f"{q} latest news",
            f"{q} official update",
            f"{q} SEC filing",
            f"{q} launch schedule delivery update",
        ]

    if category == "entertainment":
        return [
            q,
            f"{q} Billboard chart update",
            f"{q} Spotify chart",
            f"{q} latest entertainment news",
            f"{q} reddit",
        ]

    if category == "stocks":
        return [
            q,
            f"{q} MarketWatch CNBC Yahoo Finance",
            f"{q} stock news today",
            f"{q} earnings guidance",
            f"{q} analyst update",
        ]

    return [
        q,
        f"{q} latest news",
        f"{q} today",
        f"{q} market movement",
        f"{q} reddit",
    ]


def relevance_score(item, query):
    title = str(item.get("title") or "").lower()
    summary = str(item.get("summary") or "").lower()
    source = str(item.get("source") or "").lower()
    link = str(item.get("link") or "").lower()

    q_words = [
        w for w in re.findall(r"[a-zA-Z0-9]+", query.lower())
        if len(w) >= 3
    ]

    score = 0

    for word in q_words:
        if word in title:
            score += 5
        if word in summary:
            score += 2

    if any(domain in link for domain in TRUSTED_DOMAINS):
        score += 8

    if "reddit" in source.lower():
        score += 2

    if item.get("published"):
        score += 2

    return score


def google_news_search(query, limit=MAX_RESULTS_PER_SOURCE):
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query + ' when:2d')}&hl=en-US&gl=US&ceid=US:en"
    )

    feed = feedparser.parse(url)
    results = []

    for entry in feed.entries[:limit]:
        results.append({
            "source": "Google News",
            "title": clean_html(entry.get("title", "")),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": clean_html(entry.get("summary", "")),
        })

    return results


def gdelt_search(query, limit=MAX_RESULTS_PER_SOURCE):
    url = "https://api.gdeltproject.org/api/v2/doc/doc"

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": limit,
        "sort": "DateDesc",
    }

    r = safe_get(url, params=params)

    if not r:
        return []

    try:
        data = r.json()
    except Exception:
        return []

    results = []

    for item in data.get("articles", [])[:limit]:
        results.append({
            "source": "GDELT News",
            "title": clean_html(item.get("title", "")),
            "link": item.get("url", ""),
            "published": item.get("seendate", ""),
            "summary": item.get("domain", ""),
        })

    return results


def reddit_search(query, limit=MAX_RESULTS_PER_SOURCE):
    url = "https://www.reddit.com/search.json"

    params = {
        "q": query,
        "sort": "new",
        "t": "day",
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
            "source": f"Reddit r/{d.get('subreddit', '')}",
            "title": clean_html(d.get("title", "")),
            "link": "https://reddit.com" + d.get("permalink", ""),
            "published": "",
            "summary": f"Score: {d.get('score', 0)} | Comments: {d.get('num_comments', 0)}",
        })

    return results


def coingecko_search(query):
    coins = {
        "bitcoin": "bitcoin",
        "btc": "bitcoin",
        "ethereum": "ethereum",
        "eth": "ethereum",
        "solana": "solana",
        "sol": "solana",
    }

    q = query.lower()
    coin_id = None

    for key, value in coins.items():
        if key in q:
            coin_id = value
            break

    if not coin_id:
        return []

    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
    }

    r = safe_get(url, params=params)

    if not r:
        return []

    try:
        data = r.json()
        item = data.get(coin_id, {})
        price = item.get("usd")
        change = item.get("usd_24h_change")
        volume = item.get("usd_24h_vol")
    except Exception:
        return []

    if price is None:
        return []

    return [{
        "source": "CoinGecko",
        "title": f"{coin_id.upper()} market data",
        "link": f"https://www.coingecko.com/en/coins/{coin_id}",
        "published": "live",
        "summary": f"Price: ${price:,.2f} | 24h Change: {change:.2f}% | Volume: ${volume:,.0f}",
    }]


def coinbase_search(query):
    symbols = ["BTC", "ETH", "SOL"]
    q = query.lower()

    matched = []

    for symbol in symbols:
        if symbol.lower() in q:
            matched.append(symbol)
        elif symbol == "BTC" and "bitcoin" in q:
            matched.append(symbol)
        elif symbol == "ETH" and "ethereum" in q:
            matched.append(symbol)
        elif symbol == "SOL" and "solana" in q:
            matched.append(symbol)

    results = []

    for symbol in matched:
        url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
        r = safe_get(url)

        if not r:
            continue

        try:
            data = r.json()
            price = float(data["data"]["amount"])
        except Exception:
            continue

        results.append({
            "source": "Coinbase",
            "title": f"{symbol} live spot price",
            "link": f"https://www.coinbase.com/price/{symbol.lower()}",
            "published": "live",
            "summary": f"{symbol}: ${price:,.2f}",
        })

    return results


def ai_search(query):
    all_results = []

    all_results.extend(coingecko_search(query))
    all_results.extend(coinbase_search(query))

    for q in build_queries(query):
        all_results.extend(google_news_search(q, limit=3))
        all_results.extend(gdelt_search(q, limit=3))

    all_results.extend(reddit_search(query, limit=5))

    seen = set()
    clean = []

    for item in all_results:
        key = (item.get("title", ""), item.get("link", ""))
        if key in seen:
            continue

        item["relevance"] = relevance_score(item, query)

        if item["relevance"] < 4:
            continue

        seen.add(key)
        clean.append(item)

    clean = sorted(clean, key=lambda x: x.get("relevance", 0), reverse=True)

    return clean[:MAX_FINAL_RESULTS]


def edge_read(query, results):
    if not results:
        return "No strong outside-source confirmation found."

    top_sources = [r.get("source", "") for r in results[:5]]
    live_count = sum(1 for r in results if r.get("published") == "live")
    reddit_count = sum(1 for r in results if "Reddit" in r.get("source", ""))

    read = []

    read.append(f"Results Found: {len(results)}")
    read.append(f"Top Sources: {', '.join(top_sources)}")

    if live_count:
        read.append(f"Live Market Data Sources: {live_count}")

    if reddit_count:
        read.append(f"Reddit/Social Mentions: {reddit_count}")

    if len(results) >= 8:
        read.append("Broad Confirmation: Strong")
    elif len(results) >= 4:
        read.append("Broad Confirmation: Moderate")
    else:
        read.append("Broad Confirmation: Weak")

    return "\n".join(read)


def print_ai_search(query):
    print("\nAI-STYLE BROAD SEARCH")
    print(f"Query: {query}")
    print(f"Category: {detect_category(query)}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("-" * 70)

    results = ai_search(query)

    print("EDGE READ")
    print(edge_read(query, results))
    print("-" * 70)

    if not results:
        print("No trusted source results found.")
        return

    for i, item in enumerate(results, start=1):
        print("-" * 70)
        print(f"#{i}")
        print(f"Relevance: {item.get('relevance')}")
        print(f"Source: {item.get('source')}")
        print(f"Title: {item.get('title')}")
        if item.get("published"):
            print(f"Published: {item.get('published')}")
        print(f"Link: {item.get('link')}")
        summary = str(item.get("summary") or "").replace("\n", " ")
        if summary:
            print(f"Summary: {summary[:500]}")


if __name__ == "__main__":
    query = input("AI Search Query: ").strip()
    print_ai_search(query)