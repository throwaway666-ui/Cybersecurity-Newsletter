"""
bot/twitter.py
──────────────
Utility for pulling the hottest Twitter/X topics via twitterapi.io.

• Calls  GET /twitter/trends  (documented here → docs.twitterapi.io)
• Requires the header  X‑API‑Key: <your key>
• Returns a plain‑Python list of the top N trend strings, stripped of '#'
"""

from __future__ import annotations

import os
import requests
from typing import List

# ---------------------------------------------------------------------------

API_KEY: str = os.environ["TWITTERAPI_KEY"]     # ←  add as GitHub Secret
BASE_URL: str = "https://api.twitterapi.io"

# ---------------------------------------------------------------------------


def fetch_top_terms(count: int = 5, woeid: int = 1) -> List[str]:
    """
    Return the first `count` worldwide trends (woeid = 1) as simple strings.

    twitterapi.io sample response  (Docs 07‑2025) ﻿:contentReference[oaicite:0]{index=0}
    {
        "trends": [
            { "name": "#CyberSecurity", "rank": 1, ... },
            { "name": "#Malware",       "rank": 2, ... }
        ],
        "status": "success"
    }

    Some live responses use the key `trend` instead of `name`, so we check both.
    """
    url = f"{BASE_URL}/twitter/trends"
    headers = {"x-api-key": API_KEY}
    params = {"woeid": woeid, "count": count}

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()

    trends = resp.json().get("trends", [])[:count]

    def _extract(item: dict) -> str:
        raw = item.get("name") or item.get("trend") or ""
        return raw.lstrip("#")

    return [_extract(t) for t in trends if _extract(t)]


# Simple manual test (uncomment to run locally)
# if __name__ == "__main__":
#     print(fetch_top_terms())
