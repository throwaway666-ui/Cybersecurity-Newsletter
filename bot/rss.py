"""
bot/rss.py  –  Collect headlines and descriptions from the past 24 hours from 3 RSS feeds.
"""

from __future__ import annotations
import datetime, feedparser
from typing import List, Dict

FEEDS = [
    "https://krebsonsecurity.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://securityaffairs.com/feed",
]

def today_items(max_items: int = 25, hours_back: int = 24) -> List[Dict[str, str]]:
    """Return a list of dicts: {title, summary} for items in the past `hours_back` hours."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours_back)
    items = []

    for url in FEEDS:
        fp = feedparser.parse(url)
        for e in fp.entries:
            stamp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if not stamp:
                continue
            entry_dt = datetime.datetime(*stamp[:6], tzinfo=datetime.timezone.utc)
            if entry_dt >= cutoff:
                title = e.title.strip()
                summary = getattr(e, "summary", "") or getattr(e, "description", "")
                items.append({"title": title, "summary": summary.strip()})

    # Deduplicate by title while preserving order
    seen, unique = set(), []
    for item in items:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)

    return unique[:max_items]
