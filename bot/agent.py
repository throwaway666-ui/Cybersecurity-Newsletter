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

def rewrite_title_with_gemini(title: str, summary: str = "") -> str:
    """Use Gemini to rewrite the title into a punchy headline."""
    try:
        genai.configure(api_key=GENAI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = (
            "You are a cybersecurity editor."
            " Rewrite this news headline to make it short, punchy, and clear."
            " Add an appropriate emoji (e.g., 🚨 for CVEs, 🛡️ for patches, 📊 for reports)."
            " Avoid duplicate words and keep it professional."
            f"\n\nTitle: {title}\n"
            f"Summary: {summary[:300]}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("⚠️ Gemini error:", e)
        return title  # fallback

# ── Main routine ───────────────────────────────────────────────────
if __name__ == "__main__":
    t0 = time.time()
    try:
        # 1) Get RSS items (title, summary, link, image)
        rss_items = today_items(max_items=8)

        # 2) Assemble HTML content
        today_str = datetime.date.today().strftime("%d %b %Y")
        html_items = ""
        plain_items = ""

        for item in rss_items:
            original_title = item.get("title", "No title")
            summary = item.get("summary", "")
            link = item.get("link", "")
            image = item.get("image", "")

            # Rewrite title using Gemini
            title = rewrite_title_with_gemini(original_title, summary)

            # Highlight CVE IDs
            title = re.sub(r"(CVE-\d{4}-\d+)", r"<strong>[\1]</strong>", title)
            summary = re.sub(r"(CVE-\d{4}-\d+)", r"<strong>[\1]</strong>", summary)

            html_items += f"""
            <div style='margin-bottom:30px;'>
              {f'<img src="{image}" alt="news image" style="width:100%; border-radius:12px; margin:12px 0;" />' if image else ''}
              <h2 style='font-size:20px; color:#ffffff; font-weight:600; margin:4px 0;'>
                <a h
