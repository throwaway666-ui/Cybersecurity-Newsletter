"""
bot/rss.py
──────────
Collect today's items from a list of RSS/Atom feeds.
"""

from __future__ import annotations
import datetime, feedparser, urllib.parse
from typing import List

FEEDS = [
    "https://krebsonsecurity.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://securityaffairs.com/feed",
]

def today_items(max_items: int = 20, timezone: datetime.timezone | None = None) -> List[str]:
    """Return titles (optionally title + link) of items dated 'today'."""
    tz     = timezone or datetime.timezone.utc
    today  = datetime.datetime.now(tz).date()
    titles = []

    for url in FEEDS:
        fp = feedparser.parse(url)
        for e in fp.entries:
            # feedparser's parsed date is in .published_parsed or .updated_parsed
            stamp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if not stamp:
                continue
            item_date = datetime.date(stamp.tm_year, stamp.tm_mon, stamp.tm_mday)
            if item_date == today:
                title = e.title.strip()
                # Optionally append URL: title += f" ({e.link})"
                titles.append(title)

    # Deduplicate & cap
    seen, dedup = set(), []
    for t in titles:
        if t not in seen:
            seen.add(t); dedup.append(t)
    return dedup[:max_items]
