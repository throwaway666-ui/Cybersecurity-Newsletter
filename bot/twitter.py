"""
bot/twitter.py
──────────────
Return up to five trending cybersecurity terms via twitterapi.io.

Strategy:
1️⃣  Call  /twitter/trends   (woeid = 1, world‑wide)
    • If it returns ≥1 items → use the first five.
2️⃣  Otherwise fall back to  /twitter/search
    • Query popular tweets for core infosec keywords
    • Pick the five most‑mentioned keywords.
"""

from __future__ import annotations
import os, requests, collections
from typing import List

API_KEY  = os.environ["TWITTERAPI_KEY"]
if not API_KEY:
    raise RuntimeError("TWITTERAPI_KEY env‑var missing")

BASE_URL = "https://api.twitterapi.io"

CYBER_WORDS = [
    "ransomware", "phishing", "malware",
    "zero‑day", "infosec", "CVE", "cybersecurity"
]

def _extract_term(item: dict) -> str:
    raw = item.get("name") or item.get("trend") or ""
    return raw.lstrip("#") if isinstance(raw, str) else ""

def fetch_top_terms(count: int = 5, woeid: int = 1) -> List[str]:
    # ── 1) Try /twitter/trends ────────────────────────────────────────────
    url  = f"{BASE_URL}/twitter/trends"
    head = {"x-api-key": API_KEY}
    resp = requests.get(url, headers=head, params={"woeid": woeid}, timeout=15)
    if resp.status_code == 200:
        trends = resp.json().get("trends", [])
        terms  = [_extract_term(t) for t in trends if _extract_term(t)]
        if terms:
            return terms[:count]

    # ── 2) Fallback: /twitter/search for popular tweets ──────────────────
    query = " OR ".join(CYBER_WORDS)
    s_url = f"{BASE_URL}/twitter/search"
    s_par = {"q": query, "result_type": "popular", "count": 100}
    s_resp = requests.get(s_url, headers=head, params=s_par, timeout=15)
    if s_resp.status_code == 200:
        texts = " ".join(t["text"] for t in s_resp.json().get("statuses", []))
        bag = collections.Counter()
        for kw in CYBER_WORDS:
            bag[kw] = texts.lower().count(kw)
        ranked = [kw for kw, _ in bag.most_common(count) if bag[kw] > 0]
        if ranked:
            return ranked

    # ── 3) Final fallback: static defaults ───────────────────────────────
    return CYBER_WORDS[:count]
