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
        return "• No fresh cybersecurity headlines found in the last 24h."

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
  <body style="margin:0; padding:0; background:#0f0f0f; font-family:'Segoe UI', Roboto, Arial, sans-serif; color:#ffffff;">
    <div style="max-width:640px; margin:40px auto; background:#121212; border-radius:16px; overflow:hidden; box-shadow:0 8px 24px rgba(0,0,0,0.3);">

      <!-- Header -->
      <div style="background:#00ffe0; color:#000000; padding:24px 32px;">
        <h1 style="margin:0; font-size:28px; font-weight:700; letter-spacing:-0.5px;">
          🕵️ Cybersecurity Digest
        </h1>
        <p style="margin:4px 0 0; font-size:14px; font-weight:500;">{today_str}</p>
      </div>

      <!-- Twitter Trends -->
      <div style="padding:32px;">
        <h2 style="color:#00ffe0; font-size:20px; font-weight:600; margin-top:0;">📈 Trending Topics on Twitter</h2>
        <ul style="padding-left:20px; font-size:16px; line-height:1.8; color:#e0e0e0;">
          {''.join(f'<li>{t}</li>' for t in twitter_terms)}
        </ul>
      </div>

      <!-- Cyber News -->
      <div style="background:#1e1e1e; padding:32px;">
        <h2 style="color:#ffffff; font-size:20px; font-weight:600;">📰 Today’s Cybersecurity Headlines</h2>
        <ul style="padding-left:20px; font-size:16px; line-height:1.8; color:#cccccc;">
          {''.join(f'<li>{line.lstrip("• ").strip()}</li>' for line in news_block.splitlines() if line.strip())}
        </ul>
      </div>

      <!-- Footer -->
      <div style="text-align:center; padding:20px 0; font-size:12px; color:#888888;">
        Stay secure. This digest was sent by your automated cybersecurity agent.<br>
        <span style="color:#555;">© {today_str[:4]} Cyber Digest Bot</span>
      </div>

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
