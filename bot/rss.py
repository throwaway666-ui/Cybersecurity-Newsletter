from __future__ import annotations
import datetime, feedparser, re
from typing import List, Dict

FEEDS = [
    "https://krebsonsecurity.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://securityaffairs.com/feed",
]

def extract_image(entry) -> str:
    # Try standard media:content image
    if "media_content" in entry:
        for media in entry.media_content:
            if "url" in media:
                return media["url"]

    # Try in summary HTML using regex
    summary = entry.get("summary", "")
    match = re.search(r'<img[^>]+src="([^"]+)"', summary)
    if match:
        return match.group(1)

    return ""  # fallback

def today_items(max_items: int = 25, hours_back: int = 24) -> List[Dict[str, str]]:
    """Return recent RSS items with title, summary, link, and image."""
    import datetime
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours_back)
    items = []

    for url in FEEDS:
        fp = feedparser.parse(url)
        for e in fp.entries:
            stamp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if not stamp:
                continue
            entry_dt = datetime.datetime(*stamp[:6], tzinfo=datetime.timezone.utc)
            if entry_dt < cutoff:
                continue

            title = e.get("title", "").strip()
            summary = re.sub(r'<.*?>', '', e.get("summary", "")).strip()  # strip HTML
            link = e.get("link", "").strip()
            image = extract_image(e)

            items.append({
                "title": title,
                "summary": summary,
                "link": link,
                "image": image,
            })

    # Deduplicate
    seen_titles = set()
    unique = []
    for item in items:
        if item["title"] not in seen_titles:
            seen_titles.add(item["title"])
            unique.append(item)

    return unique[:max_items]
