"""
bot/rss.py  –  Collect headlines from the past 24 hours from 3 RSS feeds.
"""

from __future__ import annotations
import datetime, feedparser
from typing import List

FEEDS = [
    "https://krebsonsecurity.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://securityaffairs.com/feed",
]

def today_items(max_items: int = 25, hours_back: int = 24) -> List[str]:
    """Return headlines from the past `hours_back` hours (default: 24h)."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours_back)
    titles = []

    for url in FEEDS:
        fp = feedparser.parse(url)
        for e in fp.entries:
            stamp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if not stamp:
                continue
            entry_dt = datetime.datetime(*stamp[:6], tzinfo=datetime.timezone.utc)
            if entry_dt >= cutoff:
                titles.append(e.title.strip())

    # Deduplicate while preserving order
    seen, unique = set(), []
    for t in titles:
        if t not in seen:
            seen.add(t); unique.append(t)
    return unique[:max_items]
