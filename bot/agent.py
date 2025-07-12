"""
bot/agent.py
────────────
Daily workflow:

1. Get top Twitter/X trends via twitterapi.io  (fetch_top_terms)
2. Ask Gemini‑Flash‑2.5 for a 5‑bullet cybersecurity brief
3. Post the digest to a Telegram channel
   • TG_TOKEN, TG_CHAT_ID, GENAI_API_KEY, TWITTERAPI_KEY are GitHub secrets
"""

from __future__ import annotations
import os, datetime, requests, sys, traceback
import google.generativeai as genai
from twitter import fetch_top_terms


# ── Environment variables ----------------------------------------------------
TG_TOKEN      = os.environ["TG_TOKEN"]        # BotFather token
TG_CHAT_ID    = os.environ["TG_CHAT_ID"]      # @channel or -100…
GENAI_API_KEY = os.environ["GENAI_API_KEY"]   # Google AI API key
# -----------------------------------------------------------------------------


def make_digest(terms: list[str]) -> str:
    """Use Gemini‑Flash‑2.5 to turn terms into a 5‑bullet digest."""
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    today = datetime.date.today().strftime("%d %b %Y")
    prompt = (
        "You are a cybersecurity analyst.\n"
        f"Trending terms: {', '.join(terms)}.\n"
        "Produce exactly five concise bullets (≈25 words each) explaining why each term is trending. "
        "Return plain text, bullets prefixed with '•', no hashtags, no markdown."
    )
    resp = model.generate_content(prompt)
    return f"🕵️‍♂️ Cybersecurity trends — {today}\n\n{resp.text.strip()}"


def send_to_telegram(message: str) -> None:
    """Post `message` to Telegram; print response for debugging."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        # "parse_mode": "Markdown",   # enable later when message format is solid
    }

    response = requests.post(url, json=payload, timeout=15)
    print("Telegram API response:", response.status_code, response.text[:300])
    response.raise_for_status()   # will raise if status != 2xx


if __name__ == "__main__":
    try:
        top_terms = fetch_top_terms()
        digest    = make_digest(top_terms)

        print("===== Gemini Digest Output =====")
        print(digest)
        print("================================================================")

        send_to_telegram(digest)
        print("✅  Digest sent to Telegram successfully.")

    except Exception as e:
        # Print full traceback to GitHub Actions log for easier debugging
        traceback.print_exc()
        sys.exit(1)
