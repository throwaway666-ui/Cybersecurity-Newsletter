from __future__ import annotations
import os, datetime, requests, sys, traceback, time
import google.generativeai as genai
import re # Added to support re.sub for plain text digest

from rss import today_items
from send_email import send_html_email # custom Gmail sender

# ── Secrets / env vars ─────────────────────────────────────────────
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]
GENAI_API_KEY = os.environ["GENAI_API_KEY"]
# GMAIL secrets are handled inside email.py via env vars
# ───────────────────────────────────────────────────────────────────

def summarise_rss(articles: list[dict], bullets: int = 5) -> str:
    """Use Gemini to generate custom titles and bullet-point summaries from article title + summary."""
    if not articles:
        return "• No fresh cybersecurity headlines found in the last\u202f24h."

    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    results = []
    for article in articles[:bullets]:
        cve_hint = (
            "Highlight CVE IDs in square brackets like [CVE-2025-1234]. "
            if "cve" in article["title"].lower() or article["summary"].lower() else ""
        )

        prompt = (
            "You are a cybersecurity editor. For the following news article, "
            "first write a short, punchy title including appropriate emojis. "
            "Then, provide 2-3 **very concise, impactful bullet points** summarizing the key takeaways. "
            f"{cve_hint}"
            "Avoid hashtags, links, or conversational filler.\n\n"
            f"Title: {article['title']}\n"
            f"Description: {article['summary']}"
        )

        try:
            response = model.generate_content(prompt)
            generated_content = response.text.strip()

            lines = generated_content.splitlines()
            final_title = article['title']
            rundown_text = ""
            details_html = ""

            if lines:
                potential_title = lines[0].strip()
                if potential_title.lower().startswith("title:"):
                    final_title = potential_title[len("title:"):].strip()
                elif potential_title:
                    final_title = potential_title

                content_lines = lines[1:]

                for i, line in enumerate(content_lines):
                    stripped_line = line.strip()
                    if stripped_line and not (stripped_line.startswith('*') or stripped_line.startswith('-')):
                        rundown_text = stripped_line
                        content_lines = content_lines[i+1:]
                        break

                bullet_points = []
                for line in content_lines:
                    stripped_line = line.strip()
                    if stripped_line and (stripped_line.startswith('*') or stripped_line.startswith('-') or len(stripped_line) > 10):
                        bullet_points.append(stripped_line.strip('* ').strip('- ').strip())

                if bullet_points:
                    bullet_points_html_content = "".join([
                        f"<li style='margin-bottom:8px;'>{bp}</li>"
                        for bp in bullet_points if bp
                    ])
                    if bullet_points_html_content:
                        details_html = f"<ul style='padding-left:20px; margin:0; list-style-type:disc; color:#cccccc; font-size:15px; line-height:1.6;'>{bullet_points_html_content}</ul>"

                if not details_html:
                    details_html = f"<p style='color:#cccccc; font-size:15px; line-height:1.7; margin:0;'>{article['summary']}</p>"

                if not rundown_text:
                    rundown_text = article['summary'].split('.')[0] + '.' if '.' in article['summary'] else article['summary']
                    if len(rundown_text) > 150:
                        rundown_text = rundown_text[:150] + '...'

            if not rundown_text and not details_html:
                final_summary_content = article['summary_content_html'] if article.get('summary_content_html') else f"<p style='color:#cccccc; font-size:15px; line-height:1.7; margin:0;'>{article['summary']}</p>"
            else:
                final_summary_content = (
                    f"<p style='font-weight:bold; color:#E0E0E0; font-size:16px; margin-bottom:10px; margin-top:0;'>The Rundown: <span style='font-weight:normal; color:#cccccc;'>{rundown_text}</span></p>"
                    f"<p style='font-weight:bold; color:#E0E0E0; font-size:16px; margin-bottom:10px; margin-top:15px;'>The details:</p>"
                    f"{details_html}"
                )

        except Exception as e:
            print(f"Error generating content for article '{article['title']}': {e}")
            traceback.print_exc()
            final_title = article['title']
            final_summary_content = article['summary_content_html'] if article.get('summary_content_html') else f"<p style='color:#cccccc; font-size:16px; line-height:1.7; margin-bottom:20px;'>{article['summary']}</p>"
            
        # Removed the time.sleep(60) call here
        # time.sleep(60) # This line has been removed

        results.append({
            "title": final_title,
            "summary_content_html": final_summary_content,
            "link": article['link'],
            "image_url": article.get("image_url", "")
        })

    return results

def send_to_telegram(text: str) -> None:
    """Send plain\u202ftext message to Telegram."""
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
        print(f"DEBUG: Number of raw_articles fetched: {len(raw_articles)}")
        summaries = summarise_rss(raw_articles, bullets=5)
        print(f"DEBUG: Number of summaries generated: {len(summaries)}")
        today_str = datetime.date.today().strftime("%d %b %Y")

        # --- Plain-text digest for Telegram (adapted to new structure) ---
        # Note: Aggressively stripping HTML for plain text Telegram message
        news_block = "\n\n".join([
            f"{item['title']}\n"
            f"{re.sub(r'<.*?>', '', item['summary_content_html']).strip()}" # Strip all HTML for plain text
            for item in summaries
        ])
        digest = f"🕵️\u200b♂️ Cybersecurity Digest \u2014 {today_str}\n\n{news_block}"
        # -------------------------------------------------------------------

        # Generate Quick Links section
        quick_links = "\n".join([
            f"<li><a href=\"{item['link']}\" style=\"color:#00F5D4; text-decoration:none;\">{item['title']}</a></li>"
            for item in summaries
        ])

        html_items = ""
        for item in summaries:
            # Add image if available
            image_html = ""
            if item.get('image_url'):
                image_html = f"<img src=\"{item['image_url']}\" alt=\"{item['title']}\" style=\"width:100%; max-width:550px; height:auto; display:block; margin:0 auto 20px; border-radius:8px; object-fit:cover;\">"

            html_items += (
                f"<div style='margin-bottom:30px; padding:25px; border-radius:12px; background-color:#1E1E1E; box-shadow:0 6px 15px rgba(0,255,224,0.1);'>"
                + f"<h2 style='font-size:22px; color:#00F5D4; font-weight:700; margin:0 0 15px; line-height:1.3;'>{item['title']}</h2>"
                + image_html +
                f"{item['summary_content_html']}"
                f"<a href=\"{item['link']}\" target=\"_blank\" style=\"display:inline-block; margin-top:20px; padding:12px 25px; background-color:#00FFE0; color:#121212; text-decoration:none; border-radius:8px; font-weight:bold; font-size:15px; transition:background-color 0.3s ease;\">Read More &gt;</a>"
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
                    p, li, span {{
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
                                    🛡️ Quick Links
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
                                <h3 style="color:#FFFFFF; font-size:20px; margin-bottom:25px; font-weight:bold;">📚 Today's Stories</h3>
                                {html_items}
                            </td>
                        </tr>
                    </table>

                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#121212; border-bottom-left-radius:16px; border-bottom-right-radius:16px;">
                        <tr>
                            <td style="text-align:center; padding:25px; font-size:12px; color:#888888;">
                                <p style="margin:0 0 10px; font-size:14px; color:#cccccc;">
                                    Was this email forwarded to you? <a href="YOUR_SIGNUP_LINK_HERE" target="_blank" style="color:#00FFE0; text-decoration:underline;">Sign up for free here</a>.
                                </p>
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
        send_html_email(f"🕵️ Cybersecurity Digest \u2014 {today_str}", html_digest)

        print(f"✅ Sent to Telegram and Gmail!  Runtime: {time.time() - t0:.1f}s")

    except Exception:
        traceback.print_exc()
        sys.exit(1)
