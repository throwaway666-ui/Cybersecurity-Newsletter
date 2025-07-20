from __future__ import annotations
import datetime, feedparser, re
from typing import List, Dict
from bs4 import BeautifulSoup # Import BeautifulSoup is crucial

FEEDS = [
    "https://krebsonsecurity.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://securityaffairs.com/feed",
]

def today_items(max_items: int = 25, hours_back: int = 42) -> List[Dict[str, str]]:
    """Return recent RSS items with title, summary (plain text), link, image_url, and summary_content_html."""
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
            link = e.get("link", "").strip()

            image_url = ""
            summary_content_html = ""
            raw_summary = e.get("summary", "") # Preserve raw summary/description for processing

            # 1. Attempt to get full HTML content from 'content:encoded' first
            # feedparser typically puts content:encoded into e.content[0].value
            if 'content' in e and isinstance(e.content, list) and len(e.content) > 0 and 'value' in e.content[0]:
                summary_content_html = e.content[0].value
            elif 'content' in e and isinstance(e.content, dict) and 'value' in e.content:
                # Handle cases where e.content might be a dict directly (less common but possible)
                summary_content_html = e.content.value
            
            if summary_content_html:
                content_soup = BeautifulSoup(summary_content_html, 'html.parser')
                # Try to find the first image in the parsed HTML content
                img_tag = content_soup.find('img')
                if img_tag and 'src' in img_tag.attrs:
                    image_url = img_tag['src']
            
            # 2. If no image found yet, check 'media:content' (e.g., The Hacker News sometimes uses this)
            if not image_url and 'media_content' in e:
                for media in e.media_content:
                    if 'url' in media and media.get('type', '').startswith('image/'):
                        image_url = media['url']
                        break # Take the first valid image

            # 3. If no image found yet, check 'enclosures' (e.g., The Hacker News often uses this)
            if not image_url and 'enclosures' in e:
                for enc in e.enclosures:
                    if 'href' in enc and enc.get('type', '').startswith('image/'):
                        image_url = enc['href']
                        break # Take the first valid image

            # 4. Fallback: If no image found yet, search for an <img> tag in the raw 'summary'/'description'
            if not image_url and raw_summary:
                summary_soup_for_img = BeautifulSoup(raw_summary, 'html.parser')
                img_tag_in_summary = summary_soup_for_img.find('img')
                if img_tag_in_summary and 'src' in img_tag_in_summary.attrs:
                    image_url = img_tag_in_summary['src']
            
            # Ensure summary_content_html is always set. If content:encoded wasn't found, use raw_summary.
            if not summary_content_html and raw_summary:
                summary_content_html = raw_summary

            # Create a plain text summary for the 'summary' field (useful for previews or text-only display)
            plain_text_summary = re.sub(r'<.*?>', '', raw_summary).strip()


            items.append({
                "title": title,
                "summary": plain_text_summary, # This is the plain text summary
                "link": link,
                "image_url": image_url,       # The extracted image URL
                "summary_content_html": summary_content_html, # The HTML content for the digest
            })

    # Deduplicate items by title to avoid duplicates from multiple feeds or feed updates
    seen_titles = set()
    unique = []
    for item in items:
        if item["title"] not in seen_titles:
            seen_titles.add(item["title"])
            unique.append(item)

    return unique[:max_items]
