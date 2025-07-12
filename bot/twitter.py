"""
twitter.py  —  helper for twitterapi.io

• Pulls recent English tweets that mention core cybersecurity terms
• Weights each term by likes + retweets
• Returns the 5 hottest terms of the last 24 h
"""

import os, datetime, requests
from collections import Counter

API_KEY  = os.environ["TWITTERAPI_KEY"]          # ← GitHub secret
BASE_URL = "https://api.twitterapi.io"           # per docs

# ---------------------------------------------------------------------------

CYBER_WORDS = [
    "cybersecurity", "infosec", "ransomware",
    "zero-day", "phishing", "malware", "CVE"
]

def _utc_iso(hours_back: int = 24) -> str:
    """ISO‑8601 timestamp X hours ago in UTC (twitterapi.io format)."""
    dt = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_back)
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat(timespec="seconds")

def fetch_top_terms(hours: int = 24, limit: int = 200):
    """
    Query twitterapi.io's /api/v2/search/recent endpoint.
    Count CYBER_WORDS occurrences weighted by engagement.
    Return top 5 terms.
    """
    since  = _utc_iso(hours)
    query  = " OR ".join(CYBER_WORDS)

    url     = f"{BASE_URL}/api/v2/search/recent"
    headers = {"x-api-key": API_KEY}             # ← REQUIRED header
    params  = {
        "query":        query,
        "start_time":   since,
        "max_results":  100,
        "tweet.fields": "public_metrics",
        "limit":        limit,
        "lang":         "en",
    }

    bag = Counter()
    fetched = 0

    while url and fetched < limit:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for tw in data.get("data", []):
            text    = tw["text"].lower()
            metrics = tw["public_metrics"]
            weight  = metrics["like_count"] + metrics["retweet_count"]

            for word in CYBER_WORDS:
                if word in text:
                    bag[word] += weight

        fetched += len(data.get("data", []))
        next_tok = data.get("meta", {}).get("next_token")
        url      = f"{BASE_URL}/api/v2/search/recent?next_token={next_tok}" if next_tok else None
        params   = None  # after the first page, params live in the URL

    # Return 5 hottest terms
    return [w for w, _ in bag.most_common(5)]

