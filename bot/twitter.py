"""
bot/twitter.py
──────────────
Utility for pulling the hottest Twitter/X topics via twitterapi.io.
"""

import os
import requests
from typing import List

API_KEY = os.environ["TWITTERAPI_KEY"]
BASE_URL = "https://api.twitterapi.io"

def fetch_top_terms(count: int = 5, woeid: int = 1) -> List[str]:
    """
    Fetch top Twitter trending topics from twitterapi.io
    Handles both 'name' and 'trend' keys gracefully.
    """
    url = f"{BASE_URL}/twitter/trends"
    headers = {"x-api-key": API_KEY}
    params = {"woeid": woeid, "count": count}

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()

    trends = resp.json().get("trends", [])[:count]

    def _extract(item: dict) -> str:
        raw = item.get("name") or item.get("trend") or ""
        return raw.lstrip("#") if isinstance(raw, str) else ""

    return [_extract(t) for t in trends if _extract(t)]
