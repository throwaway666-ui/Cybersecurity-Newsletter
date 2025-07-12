"""
agent.py
Runs daily:
  • pulls top cyber terms from twitter.py
  • asks Gemini Flash 2.5 for a short brief
  • posts it to a Telegram channel
"""

import os, datetime, requests, google.generativeai as genai
from twitter import fetch_top_terms

# --- environment variables (set these as GitHub Secrets) --------------------
TG_TOKEN   = os.environ["TG_TOKEN"]           # BotFather token
TG_CHAT_ID = os.environ["TG_CHAT_ID"]         # @channel or -100…
GENAI_KEY  = os.environ["GENAI_API_KEY"]      # Google AI key

# ---------------------------------------------------------------------------

def make_digest(terms):
    """
    Ask Gemini Flash 2.5 to write a 5‑bullet digest (~25 words each)
    explaining why each term is trending.
    """
    genai.configure(api_key=GENAI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    today = datetime.date.today().strftime("%d %b %Y")
    prompt = (
        "You are a cybersecurity analyst.\n"
        f"Today is {today}.\n"
        f"Trending terms: {', '.join(terms)}.\n"
        "For each term, write one concise bullet (~25 words) explaining why it is trending. "
        "Return exactly five bullets, no hashtags, no markdown."
    )
    resp = model.generate_content(prompt)
    return f"🕵️‍♂️ *Cybersecurity trends — {today}*\n\n" + resp.text.strip()

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()

if __name__ == "__main__":
    top_terms = fetch_top_terms()
    digest    = make_digest(top_terms)
    send_to_telegram(digest)
