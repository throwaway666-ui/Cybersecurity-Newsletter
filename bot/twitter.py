"""
twitter.py
A minimal helper around twitterapi.io to pull trending cybersecurity‑related hashtags
and return the top 5 terms weighted by engagement.
"""

import os, datetime, requests
from collections import Counter
from dateutil import tz

API_KEY   = os.environ["TWITTERAPI_KEY"]           # add this as a GitHub secret
BASE_URL  = "https://api.twitterapi.io"

# --- core cyber keywords we care about
CYBER_WORDS = [
    "cybersecurity", "infosec", "ransomware",
    "zero-day", "phishing", "malware", "CVE"
]

def _utc_iso(hours_back: int = 24) -> str:
    """Return an ISO‑8601 timestamp X hours ago in UTC."""
    dt = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_back)
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat(timespec="seconds")

def fetch_top_terms(hours: int = 24, limit: int = 200):
    """
    Call twitterapi.io recent‑tweets endpoint, filter for CYBER_WORDS,
    weight by like+retweet counts, return 5 hottest terms.
    """
    since = _utc_iso(hours)
    query = " OR ".join(CYBER_WORDS)

    url  = f"{BASE_URL}/v2/search/recent"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params  = {
        "query": query,
        "start_time": since,
        "max_results": 100,
        "tweet.fields": "public_metrics",
        "limit": limit,
    }

    bag = Counter()

    # twitterapi.io paginates via `next_token`
    while url and len(bag) < limit:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        for tw in data.get("data", []):
            text = tw["text"].lower()
            weight = tw["public_metrics"]["like_count"] + tw["public_metrics"]["retweet_count"]
            for word in CYBER_WORDS:
                if word in text:
                    bag[word] += weight

        url = f"{BASE_URL}{data['meta'].get('next_token')}" if data["meta"].get("next_token") else None
        params = None  # next requests already has pagination token in URL

    # return 5 most talked‑about terms
    return [w for w, _ in bag.most_common(5)]

