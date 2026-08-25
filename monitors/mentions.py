from urllib.parse import quote_plus

import feedparser

NEWS_FEED_URL = "https://news.google.com/rss/search?q={query}&hl=ru&gl=RU&ceid=RU:ru"
MAX_RESULTS = 15


def fetch_mentions(keyword: str) -> list[dict]:
    url = NEWS_FEED_URL.format(query=quote_plus(keyword))
    feed = feedparser.parse(url)

    results = []
    for entry in feed.entries[:MAX_RESULTS]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        if title and link:
            results.append({"title": title, "link": link})

    return results
