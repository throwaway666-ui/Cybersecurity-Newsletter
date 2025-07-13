"""
bot/agent.py
────────────
Daily workflow:
1. Get today's trending Twitter/X topics via twitterapi.io      (fetch_top_terms)
2. Pull today's headlines from three RSS feeds                  (rss.today_items)
3. Ask Gemini‑Flash‑2.5 to summarise the RSS headlines
4. Post both sections to a Telegram channel

Secrets required (same as before):
• TG_TOKEN        – Telegram BotFather token
• TG_CHAT_ID      – Channel ID (@user or -100…)
• GENAI_API_KEY   – Google AI key
• TWITTERAPI_KEY  – twitterapi.io key
"""

from __future__ import annotations
import os, datetime, requests, sys, traceback, time
import google.generativeai as genai
from twitter import fetch_top_terms
from rss import today_items                    # ← NEW helper

# ── Environment variables ----------------------------------------------------
TG_TOKEN      = os.environ["TG_TOKEN"]
TG_CHAT_ID    = os.environ["TG_CHAT_ID"]
GENAI_API_KEY = os.environ["GENAI_API_KEY"]
# -----------------------------------------------------------------------------


def make_rss_summary(max_bullets: int = 5) -> str:
    """Summarise today's RSS headlines into ≤ max_bullets bullets."""
    headlines = today_items(max_items=25)  # give Gemini more context than bullets
    if not headlines:
        return "No fresh cybersecurity news items were published so far today."

    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    prompt = (
        "You are a cybersecurity journalist.\n"
        "Summarise the following headlines published today into concise bullets (≤25 words each, max 5 bullets).\n"
        "Headlines:\n- " + "\n- ".join(headlines)
    )
    resp = model.generate_content(prompt)
    bullets = [line for line in resp.text.strip().splitlines() if line.strip()]
    return "\n".join(bullets[:max_bullets])


def send_to_telegram(message: str) -> None:
    """Post message to Telegram; print API response for debugging."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        # "parse_mode": "Markdown",  # enable later if message is Markdown‑safe
    }
    r = requests.post(url, json=payload, timeout=15)
    print("Telegram API response:", r.status_code, r.text[:300])
    r.raise_for_status()


if __name__ == "__main__":
    t0 = time.time()
    try:
        # ── Twitter section ────────────────────────────────────────────────
        twitter_topics = fetch_top_terms(count=5)
        twitter_block = "Trending Twitter topics (today):\n" + "\n".join(f"• {t}" for t in twitter_topics)

        # ── RSS section ────────────────────────────────────────────────────
        rss_block = "Today’s cybersecurity news highlights:\n" + make_rss_summary(max_bullets=5)

        # ── Final digest ───────────────────────────────────────────────────
        today_str = datetime.date.today().strftime("%d %b %Y")
        digest = f"🕵️‍♂️ Cybersecurity digest — {today_str}\n\n{twitter_block}\n\n{rss_block}"

        # Log and send
        print("===== Digest Output =====")
        print(digest)
        print("================================================================")
        send_to_telegram(digest)
        print(f"✅  Digest sent. Runtime: {time.time() - t0:.1f}s")

    except Exception:
        traceback.print_exc()
        sys.exit(1)
