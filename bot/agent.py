"""
bot/agent.py
────────────
Produces a Telegram + Gmail message like:

🕵‍♂️ Cybersecurity Digest — 13 Jul 2025

📈 Trending Topics on Twitter:
• Ransomware
• Phishing
• Malware
• Zero‑day
• Infosec

📰 Today’s Cybersecurity Headlines:

• 🚨 [CVE‑2025‑25257] Critical RCE vulnerability in Fortinet FortiWeb requires urgent patching.
• ⚠️ Wing FTP Server exploit in the wild after recent disclosure.
• 🧠 Security Affairs releases Issue #53 of its Malware Newsletter.
• 🌍 International Newsletter #532 published by Pierluigi Paganini (Security Affairs).
"""

from __future__ import annotations
import os, datetime, requests, sys, traceback, time, re
import google.generativeai as genai

from twitter import fetch_top_terms
from rss import today_items
from send_email import send_html_email  # custom Gmail sender

# ── Secrets / env vars ─────────────────────────────────────────────
TG_TOKEN      = os.environ["TG_TOKEN"]
TG_CHAT_ID    = os.environ["TG_CHAT_ID"]
GENAI_API_KEY = os.environ["GENAI_API_KEY"]
# GMAIL secrets are handled inside email.py via env vars
# ───────────────────────────────────────────────────────────────────


def summarise_rss(headlines: list[str], bullets: int = 5) -> str:
    """Ask Gemini Flash 2.5 to craft emoji‑enhanced news bullets."""
    if not headlines:
        return "• No fresh cybersecurity headlines found in the last 24 h."

    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    prompt = (
        "You are a cybersecurity journalist.\n"
        f"Create up to {bullets} concise, punchy bullets (~25 words each) summarizing these headlines.\n"
        "Guidelines:\n"
        "• Start each bullet with an appropriate emoji (e.g., 🚨 critical vuln, ⚠️ exploit, 🧠 analyst report, 🌍 global news).\n"
        "• Highlight CVE IDs in square brackets like [CVE-2025-1234].\n"
        "• No hashtags, no links, no markdown codes other than [CVE-…].\n\n"
        "Headlines:\n- " + "\n- ".join(headlines)
    )
    resp = model.generate_content(prompt)
    bullets_out = [ln.strip() for ln in resp.text.strip().splitlines() if ln.strip()]
    return "\n".join(bullets_out[:bullets])


def send_to_telegram(text: str) -> None:
    """Send plain‑text message to Telegram."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
    }
    r = requests.post(url, json=payload, timeout=15)
    print("Telegram API response:", r.status_code, r.text[:200])
    r.raise_for_status()


def title_case(term: str) -> str:
    """Beautify simple keywords: cve stays CVE, others capitalised."""
    if term.lower().startswith("cve"):
        return term.upper()
    return term.capitalize()


# ── Main routine ───────────────────────────────────────────────────
if __name__ == "__main__":
    t0 = time.time()
    try:
        # 1) Twitter trending topics
        twitter_terms = fetch_top_terms(count=5)
        twitter_terms = [title_case(t) for t in twitter_terms]
        twitter_block = "📈 Trending Topics on Twitter:\n" + "\n".join(f"• {t}" for t in twitter_terms)

        # 2) RSS → Gemini summary
        headlines = today_items(max_items=25)
        news_block = "📰 Today’s Cybersecurity Headlines:\n" + summarise_rss(headlines, bullets=5)

        # 3) Assemble final digest (plain-text)
        today_str = datetime.date.today().strftime("%d %b %Y")
        digest = f"🕵‍♂️ Cybersecurity Digest — {today_str}\n\n{twitter_block}\n\n{news_block}"

        # 4) Convert to HTML format
               html_digest = f"""
        <html>
          <body style="font-family:Segoe UI,Roboto,Arial,sans-serif; background:#f9f9f9; padding:20px;">
            <div style="max-width:600px; margin:auto; background:white; border-radius:10px; padding:30px; box-shadow:0 0 10px rgba(0,0,0,0.05);">
              <h2 style="color:#333333; font-size:22px; margin-top:0;">🕵️ Cybersecurity Digest — {today_str}</h2>

              <h3 style="color:#005bbb; font-size:18px; margin-bottom:10px;">📈 Trending Topics on Twitter</h3>
              <ul style="padding-left:20px; color:#222222; font-size:16px;">
                {''.join(f'<li style="margin-bottom:6px;">{t}</li>' for t in twitter_terms)}
              </ul>

              <h3 style="color:#005bbb; font-size:18px; margin-top:30px; margin-bottom:10px;">📰 Today’s Cybersecurity Headlines</h3>
              <ul style="padding-left:20px; color:#222222; font-size:16px;">
                {''.join(f'<li style="margin-bottom:10px;">{line[2:]}</li>' for line in news_block.splitlines() if line.startswith("• "))}
              </ul>

              <p style="font-size:13px; color:#888888; text-align:center; margin-top:40px;">Sent automatically via GitHub ✨</p>
            </div>
          </body>
        </html>
        """



        # 5) Log output
        print("===== Final Digest (plain-text) =====")
        print(digest)
        print("=====================================")

        # 6) Send to Telegram and Gmail
        send_to_telegram(digest)
        send_html_email(f"🕵️ Cybersecurity Digest — {today_str}", html_digest)

        print(f"✅ Sent to Telegram and Gmail!  Runtime: {time.time() - t0:.1f}s")

    except Exception:
        traceback.print_exc()
        sys.exit(1)
