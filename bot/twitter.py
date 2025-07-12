"""
twitter.py — uses twitterapi.io's /twitter/trends endpoint
"""

import os, requests

API_KEY  = os.environ["TWITTERAPI_KEY"]
BASE_URL = "https://api.twitterapi.io"

def fetch_top_terms(count=5, woeid=1):
    """
    Get top `count` trending terms for the given location (woeid=1 = worldwide)
    """
    url = f"{BASE_URL}/twitter/trends"
    headers = {"x-api-key": API_KEY}
    params = {"woeid": woeid}

    resp = requests.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()

    trends = resp.json().get("trends", [])[:count]
    return [t["name"].lstrip("#") for t in trends]
