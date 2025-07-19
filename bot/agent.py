from __future__ import annotations
import os, datetime, requests, sys, traceback, time, re
import google.generativeai as genai

from rss import today_items
from send_email import send_html_email  # custom Gmail sender

# ── Secrets / env vars ─────────────────────────────────────────────
TG_TOKEN      = os.environ["TG_TOKEN"]
TG_CHAT_ID    = os.environ["TG_CHAT_ID"]
GENAI_API_KEY = os.environ["GENAI_API_KEY"]
# ───────────────────────────────────────────────────────────────────

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

# ── Main routine ───────────────────────────────────────────────────
if __name__ == "__main__":
    t0 = time.time()
    try:
        # 1) Get RSS items (title, summary, link)
        rss_items = today_items(max_items=8)

        # 2) Assemble HTML content in headline/subheading format
        today_str = datetime.date.today().strftime("%d %b %Y")
        html_items = ""
        plain_items = ""

        for item in rss_items:
            title = item.get("title", "No title")
            summary = item.get("summary", "")
            link = item.get("link", "")

            # Highlight CVE IDs in title and summary
            title = re.sub(r"(CVE-\d{4}-\d+)", r"<strong>[\1]</strong>", title)
            summary = re.sub(r"(CVE-\d{4}-\d+)", r"<strong>[\1]</strong>", summary)

            html_items += f"""
            <div style='margin-bottom:30px;'>
              <h3 style='color:#00ffe0; font-size:16px; margin:0;'>Cyber News</h3>
              <h2 style='font-size:20px; color:#ffffff; font-weight:600; margin:4px 0;'>
                <a href="{link}" style="color:#ffffff; text-decoration:none;">{title}</a>
              </h2>
              <p style='color:#cccccc; font-size:15px; line-height:1.6; margin:0;'>
                {summary}
              </p>
              <hr style="border: none; border-top: 1px solid #333; margin:24px 0;">
            </div>
            """

            plain_items += f"🔹 {title}\n{summary}\n{link}\n\n"

        digest = f"🕵‍♂️ Cybersecurity Digest — {today_str}\n\n{plain_items.strip()}"

        # 3) Compose full HTML email
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

        # 4) Send to Telegram and Gmail
        print("===== Final Digest (plain-text) =====")
        print(digest)
        print("=====================================")

        send_to_telegram(digest)
        send_html_email(f"🕵️ Cybersecurity Digest — {today_str}", html_digest)

        print(f"✅ Sent to Telegram and Gmail!  Runtime: {time.time() - t0:.1f}s")

    except Exception:
        traceback.print_exc()
        sys.exit(1)

