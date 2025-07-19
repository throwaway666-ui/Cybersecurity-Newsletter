from __future__ import annotations
import os, datetime, requests, sys, traceback, time
import google.generativeai as genai

from rss import today_items
from send_email import send_html_email  # custom Gmail sender

# ── Secrets / env vars ─────────────────────────────────────────────
TG_TOKEN      = os.environ["TG_TOKEN"]
TG_CHAT_ID    = os.environ["TG_CHAT_ID"]
GENAI_API_KEY = os.environ["GENAI_API_KEY"]
# GMAIL secrets are handled inside email.py via env vars
# ─────────────────────────────────────────────

def summarise_rss(articles: list[dict], bullets: int = 8) -> str:
    """Use Gemini to generate custom titles from article title + summary."""
    if not articles:
        return "• No fresh cybersecurity headlines found in the last 24h."

    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    results = []
    for article in articles[:bullets]:
        cve_hint = (
            "Highlight CVE IDs in square brackets like [CVE-2025-1234]. "
            if "cve" in article["title"].lower() or "cve" in article["summary"].lower() else ""
        )

        prompt = (
            "You are a cybersecurity editor. Write a short, punchy title for the following news article. "
            "Include appropriate emojis. " + cve_hint +
            "Avoid hashtags or links.\n\n"
            f"Title: {article['title']}\n"
            f"Description: {article['summary']}"
        )

        try:
            response = model.generate_content(prompt)
            final_title = response.text.strip().splitlines()[0]
        except Exception:
            final_title = article['title']  # fallback

        results.append({
            "title": final_title,
            "summary": article['summary'],
            "link": article['link'],
            "image": article.get('image')
        })
    return results

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

# ── Main routine ─────────────────────────────────────────────
if __name__ == "__main__":
    t0 = time.time()
    try:
        # 1) Fetch RSS articles
        raw_articles = today_items(max_items=25)
        summaries = summarise_rss(raw_articles, bullets=8)

        # 2) Assemble plain-text
        today_str = datetime.date.today().strftime("%d %b %Y")
        news_block = "\n\n".join([f"{item['title']}\n{item['summary']}\n{item['link']}" for item in summaries])
        digest = f"🕵‍♂️ Cybersecurity Digest — {today_str}\n\n{news_block}"

        # 3) Convert to HTML format
        html_items = ""
        for item in summaries:
            html_items += (
                f"<div style='margin-bottom:30px;'>"
                + (f"<img src=\"{item['image']}\" alt=\"news image\" style=\"width:100%; border-radius:12px; margin:12px 0;\" />" if item.get("image") else "")
                + f"<h2 style='font-size:20px; color:#ffffff; font-weight:600; margin:4px 0;'>"
                f"<a href=\"{item['link']}\" style=\"color:#ffffff; text-decoration:none;\">{item['title']}</a></h2>"
                f"<p style='color:#cccccc; font-size:15px; line-height:1.6; margin:0;'>{item['summary']}</p>"
                f"<hr style='border: none; border-top: 1px solid #333; margin:24px 0;'>"
                f"</div>"
            )

        html_digest = f"""
        <html>
          <body style="margin:0; padding:0; background:#0f0f0f; font-family:'Segoe UI', Roboto, Arial, sans-serif; color:#ffffff;">
            <div style="max-width:640px; margin:40px auto; background:#121212; border-radius:16px; overflow:hidden; box-shadow:0 8px 24px rgba(0,0,0,0.3);">

              <!-- Header with Logo -->
              <div style="background:#00ffe0; color:#000000; padding:24px 32px; display:flex; align-items:center; gap:16px;">
                <img src="https://raw.githubusercontent.com/throwaway666-ui/Telegram-Research-Channel/main/assets/logo.png" alt="Logo" style="height:48px; border-radius:8px;" />
                <div>
                  <h1 style="margin:0; font-size:26px; font-weight:700; letter-spacing:-0.5px;">Cybersecurity Digest</h1>
                  <p style="margin:4px 0 0; font-size:14px; font-weight:500;">{today_str}</p>
                </div>
              </div>

              <!-- Cyber News -->
              <div style="background:#1e1e1e; padding:32px;">
                <h2 style="color:#ffffff; font-size:20px; font-weight:600;">📰 Today’s Cybersecurity Headlines</h2>
                {html_items}
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

        # 4) Log output
        print("===== Final Digest (plain-text) =====")
        print(digest)
        print("=====================================")

        # 5) Send to Telegram and Gmail
        send_to_telegram(digest)
        send_html_email(f"🕵️ Cybersecurity Digest — {today_str}", html_digest)

        print(f"✅ Sent to Telegram and Gmail!  Runtime: {time.time() - t0:.1f}s")

    except Exception:
        traceback.print_exc()
        sys.exit(1)
