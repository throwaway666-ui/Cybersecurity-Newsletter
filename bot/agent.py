from __future__ import annotations
import os, datetime, sys, traceback, time
import google.generativeai as genai

from rss import today_items
from send_email import send_html_email # custom Gmail sender

# ── Secrets / env vars ─────────────────────────────────────────────
GENAI_API_KEY = os.environ["GENAI_API_KEY"]
# GMAIL secrets are handled inside email.py via env vars
# ───────────────────────────────────────────────────────────────────

def generate_welcome_message(articles: list[dict]) -> str:
    """
    Use Gemini to generate a short, engaging welcome message based on the day's cybersecurity news.
    """
    if not articles:
        return "Welcome to today's Cybersecurity Digest! Stay informed and protected."

    genai.configure(api_api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Combine titles and summaries for the prompt
    news_context = ""
    for article in articles[:5]: # Use top 5 articles for context
        news_context += f"Title: {article['title']}\nSummary: {article['summary']}\n\n"

    prompt = (
        "You are a friendly and insightful cybersecurity newsletter editor. "
        "Based on the following cybersecurity news articles, write a **very short (2-3 sentences)**, "
        "engaging, and thought-provoking welcome paragraph for a daily cybersecurity digest. "
        "It should introduce the themes of today's news without being a summary itself. "
        "Use appropriate emojis. Avoid Markdown formatting for the welcome message.\n\n"
        "Here are today's headlines and summaries:\n"
        f"{news_context}"
        "Welcome message:"
    )

    try:
        response = model.generate_content(prompt)
        welcome_text = response.text.strip()
        return welcome_text if welcome_text else "Welcome to today's Cybersecurity Digest! Stay informed and protected."
    except Exception as e:
        print(f"Error generating welcome message: {e}")
        traceback.print_exc()
        return "Welcome to today's Cybersecurity Digest! Stay informed and protected."


def summarise_rss(articles: list[dict], bullets: int = 5) -> list[dict]:
    """Use Gemini to generate custom titles and bullet-point summaries from article title + summary."""
    if not articles:
        return [{"title": "No fresh cybersecurity headlines found", "summary_content_html": "<p>• No fresh cybersecurity headlines found in the last\u202f24h.</p>", "link": "#"}]

    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    results = []
    for article in articles[:bullets]:
        cve_hint = (
            "Highlight CVE IDs in square brackets like [CVE-2025-1234]. "
            if "cve" in article["title"].lower() or "cve" in article["summary"].lower() else ""
        )

        prompt = (
            "You are a cybersecurity editor. For the following news article, "
            "first write a short, punchy title including appropriate emojis, "
            "Avoid Markdowns."
            "Then, provide a **single, very concise, impactful sentence (The Radar)** summarizing the main point. " # <--- NEW LINE: Explicitly asking for "The Radar" sentence
            "Finally, provide 2-3 **very concise, impactful bullet points** summarizing the key takeaways. " # <--- MODIFIED LINE
            f"{cve_hint}"
            "Avoid hashtags, links, or conversational filler.\n\n"
            f"Title: {article['title']}\n"
            f"Description: {article['summary']}"
        )

        try:
            response = model.generate_content(prompt)
            generated_content = response.text.strip()

            lines = [line.strip() for line in generated_content.splitlines() if line.strip()] # Clean up empty lines
            final_title = article['title']
            rundown_text = ""
            details_html = ""
            bullet_points = []
            content_start_index = 0 # To track where content (radar/bullets) begins

            if lines:
                # Attempt to extract title from the first line
                potential_title = lines[0]
                if potential_title.lower().startswith("title:"):
                    final_title = potential_title[len("title:"):].strip()
                    content_start_index = 1
                elif potential_title and (potential_title.count(' ') < 10 and not (potential_title.startswith('*') or potential_title.startswith('-'))):
                    # Heuristic: if first line is short and not a bullet, assume it's the title
                    final_title = potential_title
                    content_start_index = 1
                # If content_start_index is still 0, it means the first line was not recognized as a title,
                # so we start parsing for radar/bullets from the very beginning of lines.

                # Try to find the rundown text (first non-bullet point line after potential title)
                radar_found = False
                for i in range(content_start_index, len(lines)):
                    line = lines[i]
                    if not (line.startswith('*') or line.startswith('-')) and len(line) > 10: # Assume it's rundown if not a bullet and long enough
                        rundown_text = line
                        content_start_index = i + 1 # Start looking for bullets after this
                        radar_found = True
                        break
                # If no explicit rundown found, it might be implicitly part of the content starting from content_start_index
                # We'll rely on the original summary for rundown_text if AI doesn't provide it clearly.

                # Collect bullet points from where content_start_index left off
                for i in range(content_start_index, len(lines)):
                    stripped_line = lines[i]
                    if stripped_line.startswith('*') or stripped_line.startswith('-') or len(stripped_line) > 10:
                        bullet_points.append(stripped_line.strip('* ').strip('- ').strip())

            # Construct HTML for bullet points
            if bullet_points:
                bullet_points_html_content = "".join([
                    f"<li style='margin-bottom:8px;'>{bp}</li>"
                    for bp in bullet_points if bp
                ])
                if bullet_points_html_content:
                    details_html = f"<ul style='padding-left:20px; margin:0; list-style-type:disc; color:#cccccc; font-size:15px; line-height:1.6;'>{bullet_points_html_content}</ul>"

            # Fallback for details_html if no bullets generated by AI
            if not details_html:
                details_html = f"<p style='color:#cccccc; font-size:15px; line-height:1.7; margin:0;'>{article['summary']}</p>"

            # Fallback for rundown_text if AI didn't provide it clearly.
            # No aggressive truncation here, let it be full first sentence if used.
            if not rundown_text:
                rundown_text = article['summary'].split('.')[0] + '.' if '.' in article['summary'] else article['summary']
                # Optional: You can still add a soft truncation for radar if the first sentence is excessively long
                # but aim for completeness here.
                if len(rundown_text) > 200 and not radar_found: # Only truncate if AI didn't generate one AND it's too long
                    rundown_text = rundown_text[:200] + '...'


            # Construct the final summary content HTML
            if not rundown_text and not details_html:
                final_summary_content = article['summary_content_html'] if article.get('summary_content_html') else f"<p style='color:#cccccc; font-size:15px; line-height:1.7; margin:0;'>{article['summary']}</p>"
            else:
                final_summary_content = (
                    f"<p style='font-weight:bold; color:#E0E0E0; font-size:16px; margin-bottom:10px; margin-top:0;'>The Radar: <span style='font-weight:normal; color:#cccccc;'>{rundown_text}</span></p>"
                    f"<p style='font-weight:bold; color:#E0E0E0; font-size:16px; margin-bottom:10px; margin-top:15px;'>The details:</p>"
                    f"{details_html}"
                )

        except Exception as e:
            print(f"Error generating content for article '{article['title']}': {e}")
            traceback.print_exc()
            final_title = article['title']
            # Fallback to original summary in case of any AI generation error
            final_summary_content = article['summary_content_html'] if article.get('summary_content_html') else f"<p style='color:#cccccc; font-size:16px; line-height:1.7; margin-bottom:20px;'>{article['summary']}</p>"

        results.append({
            "title": final_title,
            "summary_content_html": final_summary_content,
            "link": article['link'],
            "image_url": article.get("image_url", "")
        })

    return results

# ── Main routine ───────────────────────────────────────────────────
if __name__ == "__main__":
    t0 = time.time()
    try:
        raw_articles = today_items(max_items=25)
        print(f"DEBUG: Number of raw_articles fetched: {len(raw_articles)}")
        summaries = summarise_rss(raw_articles, bullets=5)
        print(f"DEBUG: Number of summaries generated: {len(summaries)}")
        today_str = datetime.date.today().strftime("%d %b %Y")

        # Generate the welcome message
        welcome_message = generate_welcome_message(raw_articles) # Use raw_articles for broader context

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
                        background-color: #00FFE0 !important; /* Teal for dark mode */
                        color: #000 !important; /* Black text for dark mode header */
                    }}
                    .content-block {{ /* New style for content blocks */
                        background-color: #121212 !important; /* Adjust if blocks should be lighter */
                        border: 1px solid #333333 !important;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
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
                <div style="max-width:700px; margin:0 auto;" class="email-container">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" class="header-bg" style="background-color:#00FFE0; border-top-left-radius:16px; border-top-right-radius:16px; border:1px solid #000; box-shadow:0 4px 10px rgba(0,0,0,0.3);">
                        <tr>
                            <td style="text-align:center; padding:25px 25px 20px;">
                                <img src="https://raw.githubusercontent.com/throwaway666-ui/Telegram-Research-Channel/main/assets/pnglogo.png"
                                            alt="Cybersecurity Digest Logo" style="width:100%; max-width:250px; height:auto; display:block; margin:0 auto;" />
                            </td>
                        </tr>
                        <tr>
                            <td style="text-align:center; padding:0 25px 25px;">
                                <span style="font-family:'Arial Black', Gadget, sans-serif; font-size:16px; font-weight:bold; color:#333;">{today_str}</span>
                            </td>
                        </tr>
                    </table>
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#0d0d0d; padding:20px 0;">
                        <tr>
                            <td style="padding: 0 25px;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" class="content-block" style="background-color:#121212; border-radius:12px; border:1px solid #333333; box-shadow:0 4px 10px rgba(0,0,0,0.3); margin-bottom: 20px;">
                                    <tr>
                                        <td style="padding: 25px;">
                                            <p style='color:#E0E0E0; font-size:16px; line-height:1.7; margin-top:0; margin-bottom:25px;'>
                                                {welcome_message}
                                            </p>
                                            <h3 style="color:#00FFE0; border-left:4px solid #00FFE0; padding-left:15px; font-size:18px; font-weight:bold; margin-top:0; margin-bottom:25px;">
                                                🛡️ Quick Shields
                                            </h3>
                                            <ul style="padding-left:25px; margin:0; color:#00F5D4; font-size:16px; line-height:1.8;">{quick_links}</ul>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 0 25px;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" class="content-block" style="background-color:#121212; border-radius:12px; border:1px solid #333333; box-shadow:0 4px 10px rgba(0,0,0,0.3);">
                                    <tr>
                                        <td style="padding: 25px;">
                                            <h3 style="color:#FFFFFF; font-size:20px; margin-bottom:25px; font-weight:bold;">📚 Today's Stories</h3>
                                            {html_items}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>

                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#121212; border-bottom-left-radius:16px; border-bottom-right-radius:16px;">
                        <tr>
                            <td style="text-align:center; padding:25px; font-size:12px; color:#888888;">
                                <p style="margin:0 0 10px; font-size:14px; color:#cccccc;">
                                    Was this email forwarded to you? <a href="https://github.com/throwaway666-ui/Telegram-Research-Channel" target="_blank" style="color:#00FFE0; text-decoration:underline;">Sign up for free here</a>
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

        send_html_email(f"🕵️ Cybersecurity Digest — {today_str}", html_digest)

        print(f"✅ Sent to Gmail! Runtime: {time.time() - t0:.1f}s")

    except Exception:
        traceback.print_exc()
        sys.exit(1)
