# 🕵️‍♂️ Telegram Cybersecurity Digest Bot

A fully automated, AI-powered bot that posts **daily cybersecurity digests** to a private **Telegram channel** — powered by **Twitter trends**, **RSS news**, and **Gemini 2.5 Flash summaries**. It runs entirely from **GitHub Actions** — no local execution needed.

---

## 🚀 What It Does

✅ **Twitter Trends**  
Pulls real-time cybersecurity-related trending topics using [twitterapi.io](https://docs.twitterapi.io/).

✅ **RSS News Highlights**  
Fetches latest cybersecurity news from:
- [Krebs on Security](https://krebsonsecurity.com/feed/)
- [The Hacker News](https://feeds.feedburner.com/TheHackersNews)
- [Security Affairs](https://securityaffairs.com/feed)

✅ **Gemini Flash Summarization**  
Uses **Gemini 2.5 Flash** (Google Generative AI) to summarize key headlines into 5 crisp, emoji-enhanced bullets.

✅ **Telegram Delivery**  
Automatically posts the complete digest to a Telegram channel via the Telegram Bot API.

✅ **Runs on GitHub**  
No server required. Runs daily using GitHub Actions.

---

## 🧠 Sample Output


🕵️‍♂️ Cybersecurity Digest — 13 Jul 2025

📈 Trending Topics on Twitter:
• Ransomware
• Phishing
• Malware
• Zero-day
• Infosec

📰 Today’s Cybersecurity Headlines:
• 🚨 [CVE-2025-25257] Critical RCE vulnerability in Fortinet FortiWeb requires urgent patching.
• ⚠️ Wing FTP Server exploit in the wild after recent disclosure.
• 🧠 Security Affairs releases Issue #53 of its Malware Newsletter.
• 🌍 International Newsletter #532 published by Pierluigi Paganini (Security Affairs).


---

## 📂 Project Layout

Telegram-Research-Channel/
├── bot/
│ ├── agent.py # Main controller (fetch, summarize, post)
│ ├── twitter.py # Twitter trend scraping via twitterapi.io
│ └── rss.py # RSS news parsing & filtering
└── .github/
└── workflows/
└── cyber_daily.yml # GitHub Actions workflow (daily run)

---

## 🔐 GitHub Secrets

In your repository settings, add the following secrets:

| Secret Name         | Description                                 |
|---------------------|---------------------------------------------|
| `TG_TOKEN`          | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `TG_CHAT_ID`        | Telegram channel ID (starts with `-100`)    |
| `GENAI_API_KEY`     | Google Generative AI key (for Gemini)       |
| `TWITTERAPI_KEY`    | Your API key from [twitterapi.io](https://twitterapi.io/) |

---

## ⏰ Schedule

The bot runs automatically every day at:

🕘 9:12 AM IST = 03:42 UTC
cron: '42 3 * * *'
You can also run it manually from the "Actions" tab → Run workflow.

📦 Dependencies
No setup required — GitHub Actions installs everything.
Dependencies are listed in requirements.txt, including:

requests

feedparser

google-generativeai

🙌 Credits
Created and maintained by me with technical support and code guidance from ChatGPT (GPT‑4o).
Inspired by the need for fast, reliable, daily cyber awareness.

📌 License
MIT — Free to use, adapt, and build upon.
