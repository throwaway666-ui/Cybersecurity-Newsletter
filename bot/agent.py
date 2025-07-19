from __future__ import annotations
import os, datetime, requests, sys, traceback, time
import google.generativeai as genai

from rss import today_items
from send_email import send_html_email  # custom Gmail sender

# ── Secrets / env vars ─────────────────────────────────────────────
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]
GENAI_API_KEY = os.environ["GENAI_API_KEY"]
# GMAIL secrets are handled inside email.py via env vars
# ───────────────────────────────────────────────────────────────────

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
            "image": article.get("image")
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

# ── Main routine ───────────────────────────────────────────────────
if __name__ == "__main__":
    t0 = time.time()
    try:
        raw_articles = today_items(max_items=25)
        summaries = summarise_rss(raw_articles, bullets=8)
        today_str = datetime.date.today().strftime("%d %b %Y")

        news_block = "\n\n".join([
            f"{item['title']}\n{item['summary']}\n{item['link']}"
            for item in summaries
        ])
        digest = f"🕵‍♂️ Cybersecurity Digest — {today_str}\n\n{news_block}"

        # Generate Quick Links section
        quick_links = "\n".join([
            f"<li><a href=\"{item['link']}\" style=\"color:#00F5D4; text-decoration:none;\">{item['title']}</a></li>"
            for item in summaries
        ])

        html_items = ""
        for item in summaries:
            html_items += (
                f"<div style='margin-bottom:30px; padding:25px; border-radius:12px; background-color:#1E1E1E; box-shadow:0 6px 15px rgba(0,255,224,0.1);'>"
                + (
                    f"<img src=\"{item['image']}\" alt=\"news image\" "
                    "style=\"width:100%; max-height:200px; object-fit:cover; border-radius:8px; margin-bottom:20px;\" />"
                    if item.get("image") else ""
                )
                + f"<h2 style='font-size:22px; color:#00F5D4; font-weight:700; margin:0 0 15px; line-height:1.3;'>{item['title']}</h2>"
                f"<p style='color:#cccccc; font-size:16px; line-height:1.7; margin-bottom:20px;'>{item['summary']}</p>"
                f"<a href=\"{item['link']}\" target=\"_blank\" style=\"display:inline-block; padding:12px 25px; background-color:#00FFE0; color:#121212; text-decoration:none; border-radius:8px; font-weight:bold; font-size:15px; transition:background-color 0.3s ease;\">Read More &gt;</a>"
                f"</div>"
            )

        html_digest = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Cybersecurity Digest</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #0d0d0d;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    -webkit-text-size-adjust: 100%;
                    -ms-text-size-adjust: 100%;
                }}
                table {{
                    border-spacing: 0;
                    mso-table-lspace: 0pt;
                    mso-table-rspace: 0pt;
                }}
                td {{
                    padding: 0;
                }}
                img {{
                    border: 0;
                    outline: none;
                    text-decoration: none;
                    -ms-interpolation-mode: bicubic;
                }}
                a {{
                    text-decoration: none;
                }}
                /* Dark Mode Compatibility */
                @media (prefers-color-scheme: dark) {{
                    body, .container {{
                        background-color: #0d0d0d !important;
                        color: #E0E0E0 !important;
                    }}
                    .header-bg {{
                        background-color: #00FFE0 !important;
                        color: #000 !important;
                    }}
                    .card {{
                        background-color: #1E1E1E !important;
                        box-shadow: 0 6px 15px rgba(0,255,224,0.1) !important;
                    }}
                    .cta-button {{
                        background-color: #00FFE0 !important;
                        color: #121212 !important;
                    }}
                    h1, h2, h3 {{
                        color: #00F5D4 !important;
                    }}
                    p {{
                        color: #cccccc !important;
                    }}
                }}
            </style>
        </head>
        <body style="margin:0; padding:0; background-color:#0d0d0d;">
            <center style="width:100%; background-color:#0d0d0d;">
                <div style="max-width:600px; margin:0 auto;" class="email-container">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" class="header-bg" style="background-color:#00FFE0; border-top-left-radius:16px; border-top-right-radius:16px; padding:20px;">
                        <tr>
                            <td style="padding: 20px 25px; text-align: left; display:flex; align-items:center; justify-content:space-between;">
                                <img src="https://raw.githubusercontent.com/throwaway666-ui/Telegram-Research-Channel/main/assets/logo.png"
                                     alt="logo" width="48" height="48" style="border-radius:10px; flex-shrink:0; vertical-align:middle;" />
                                <div style="text-align:right;">
                                    <h1 style="margin:0; font-size:24px; font-weight:800; color:#000; letter-spacing:-0.5px;">
                                        Cybersecurity Digest
                                    </h1>
                                    <span style="font-size:14px; font-weight:600; color:#333;">{today_str}</span>
                                </div>
                            </td>
                        </tr>
                    </table>

                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#121212; padding:25px;">
                        <tr>
                            <td style="padding: 25px 25px 0;">
                                <h3 style="color:#00FFE0; border-left:4px solid #00FFE0; padding-left:15px; font-size:18px; font-weight:bold; margin-top:0; margin-bottom:25px;">
                                    🛡️ Top Threats Today
                                </h3>
                                <ul style="padding-left:25px; margin:0; color:#00F5D4; font-size:16px; line-height:1.8;">{quick_links}</ul>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 25px 25px;">
                                <hr style="margin:0; border:0; border-top:1px solid #333333; opacity:0.6;">
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 0 25px 25px;">
                                <h3 style="color:#FFFFFF; font-size:20px; margin-bottom:25px; font-weight:bold;">📚 Deep Dive</h3>
                                {html_items}
                            </td>
                        </tr>
                    </table>

                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#121212; border-bottom-left-radius:16px; border-bottom-right-radius:16px;">
                        <tr>
                            <td style="text-align:center; padding:25px; font-size:12px; color:#888888;">
                                <p style="margin:0 0 10px;">Stay secure. This digest was sent by your automated cybersecurity agent.</p>
                                <p style="margin:0; color:#555;">&copy; {today_str[:4]} Cyber Digest Bot. All rights reserved.</p>
                                <p style="margin-top:15px;"><a href="#" style="color:#00FFE0; text-decoration:underline; font-size:11px;">Unsubscribe</a></p>
                            </td>
                        </tr>
                    </table>

                    </div>
            </center>
        </body>
        </html>
        """

        print("===== Final Digest (plain-text) =====")
        print(digest)
        print("=====================================")

        send_to_telegram(digest)
        send_html_email(f"🕵️ Cybersecurity Digest — {today_str}", html_digest)

        print(f"✅ Sent to Telegram and Gmail!  Runtime: {time.time() - t0:.1f}s")

    except Exception:
        traceback.print_exc()
        sys.exit(1)
