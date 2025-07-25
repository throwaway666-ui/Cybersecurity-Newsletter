# ✨ Cybersecurity Newsletter

## Description

This project automates the daily generation and delivery of a cybersecurity digest. It leverages GitHub Actions to run a Python-based AI agent that fetches relevant information, processes it, and then compiles and distributes a daily newsletter. This workflow ensures you stay up-to-date with the latest cybersecurity news and insights without manual effort.

## Features

* **Automated Daily Execution**: The workflow runs automatically every day at a scheduled time using GitHub Actions.

* **Manual Trigger**: Includes a `workflow_dispatch` trigger, allowing you to manually run the digest generation at any time directly from the GitHub Actions tab.

* **Content Aggregation**: The AI agent (`bot/agent.py`) is designed to fetch and process cybersecurity-related content from various sources.

* **Intelligent Content Deduplication**: Employs Jaccard similarity to identify and remove duplicate articles, ensuring a unique and concise digest.

* **AI-Powered Summarization**: Utilizes Google Generative AI (Gemini) to generate engaging welcome messages, dynamic email subject lines, and concise, bullet-point summaries for each article.

* **Flexible Delivery**: Supports delivery via multiple channels, including Telegram (though not explicitly shown in `agent.py`'s current output) and Email (Gmail).

## Getting Started

To set up and run this daily digest workflow, follow these steps:

### Prerequisites

* A GitHub account to host the repository and run GitHub Actions.

* Python 3.12 (or compatible version).

* Access to various API keys for content sources and delivery services (Telegram, Twitter, Google Generative AI, Gmail).

### Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/throwaway666-ui/Cybersecurity-Newsletter.git)
    cd your-repo-name
    ```

2.  **Install Python dependencies:**
    The workflow automatically installs dependencies, but for local development or testing, you can install them manually:

    ```bash
    pip install -r requirements.txt
    ```
    The required Python libraries are:
    * `beautifulsoup4`
    * `requests==2.32.3`
    * `google-generativeai==0.5.2`
    * `python-dateutil==2.9.0`
    * `feedparser==6.0.11`
    * `google-auth==2.29.0`
    * `google-auth-oauthlib==1.2.0`
    * `google-api-python-client==2.126.0`

### Configuration

This workflow relies heavily on GitHub Secrets to securely store sensitive API keys and credentials. You **must** add the following secrets to your GitHub repository settings (`Settings > Secrets and variables > Actions > New repository secret`):

* `GENAI_API_KEY`: Your Google Generative AI API Key (for AI agent functionalities).

* `GMAIL_REFRESH_TOKEN`: OAuth2 refresh token for your Gmail account.

* `GMAIL_CLIENT_ID`: OAuth2 client ID for your Gmail application.

* `GMAIL_CLIENT_CLIENT`: OAuth2 client secret for your Gmail application.

* `GMAIL_SENDER`: The email address from which the digest will be sent.

* `GMAIL_RECIPIENTS`: A comma-separated list of recipient email addresses for the digest.

## Workflow Details (`.github/workflows/cyber_daily.yml`)

The core automation is managed by a GitHub Actions workflow defined in `.github/workflows/cyber_daily.yml`.

* **Name**: `✨ Daily Cybersecurity Digest`

* **Triggers**:
    * `workflow_dispatch`: Allows manual triggering of the workflow from the "Actions" tab in your GitHub repository.
    * `schedule`: Automatically runs the workflow every day at `03:45 UTC` (which is `09:15 IST` / Indian Standard Time). The cron expression `45 3 * * *` specifies this schedule.

* **Jobs**:
    * `build`: This job runs on an `ubuntu-latest` environment.
    * **Steps**:
        1.  **`📂 Checkout repo`**: Checks out your repository code.
        2.  **`📁 Set up Python 3.12`**: Configures the runner with Python version 3.12.
        3.  **`📦 Install dependencies`**: Installs all required Python packages listed in `requirements.txt`.
        4.  **`🤖 Run AI Agent`**: Executes the main Python script `bot/agent.py`. All necessary API keys and credentials are passed as environment variables from GitHub Secrets to this step.

## Bot Script (`bot/agent.py`)

This Python script is the brain of the operation, orchestrating the content gathering, processing, and distribution.

* **Content Fetching**: Utilizes the `rss` module (specifically `bot/rss.py`) to gather raw articles.

* **Deduplication**: Implements a robust deduplication mechanism using Jaccard similarity to prevent redundant content. It tokenizes and normalizes article titles and summaries, comparing them against already processed articles to ensure only unique content is included.

* **AI-Powered Content Generation**:
    * **Welcome Message**: Generates a short, engaging welcome message for the newsletter using Google's Gemini model, setting the tone based on the day's top cybersecurity news.
    * **Email Subject Line**: Crafts a dynamic, punchy, and click-worthy email subject line, incorporating a relevant emoji and focusing on the most impactful news.
    * **Article Summaries**: For each selected article, Gemini generates a concise, emoji-prefixed title, a single impactful summary sentence, and 2-3 bullet points detailing key takeaways. It also highlights CVE IDs where relevant.

* **Email Formatting and Sending**:
    * Constructs a visually appealing HTML email digest with a dark theme, responsive design, and clear calls to action.
    * Includes a prominent logo from `assets/digest.png`.
    * Organizes content into "Quick Shields" (quick links) and "Today's Stories" (detailed summaries).
    * Sends the generated HTML email using a custom Gmail sender (`send_email.py`).

## RSS Feed Handler (`bot/rss.py`)

This Python script is responsible for fetching and parsing the RSS feeds to gather the raw cybersecurity news articles.

* **Feeds Processed**: It pulls articles from the following prominent cybersecurity news sources:
    * `https://krebsonsecurity.com/feed/`
    * `https://feeds.feedburner.com/TheHackersNews`
    * `https://www.bleepingcomputer.com/feed/`

* **Recent Articles**: The `today_items` function fetches articles published within a specified `hours_back` period (defaulting to 42 hours) and limits the total number of items returned (`max_items`, defaulting to 25).

* **Data Extraction**: For each RSS entry, it extracts:
    * `title`: The title of the article.
    * `summary`: A plain text version of the article's summary/description.
    * `link`: The URL to the full article.
    * `image_url`: Attempts to extract a relevant image URL from the RSS entry's content, media enclosures, or summary HTML.
    * `summary_content_html`: The full HTML content of the article's summary or description, used for richer display in the digest.

* **Initial Deduplication**: Performs a basic deduplication by title to remove exact title matches that might come from multiple feeds or feed updates before passing them to the main agent for more advanced content-based deduplication.

## Email Sender (`bot/send_email.py`)

This Python script handles the authentication and sending of the generated HTML email digest via Gmail.

* **Gmail API Integration**: It uses the `googleapiclient` library to interact with the Gmail API.

* **OAuth2 Authentication**: Authenticates with Gmail using OAuth2 credentials (`GMAIL_REFRESH_TOKEN`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`) obtained from environment variables (GitHub Secrets). This secure method allows the application to send emails on behalf of the configured Gmail account without requiring its password.

* **Email Construction**:
    * Creates a `MIMEMultipart` email message to support both plain text and HTML content, ensuring broad compatibility across email clients.
    * Sets the subject, sender (`GMAIL_SENDER`), and a visible 'To:' address (which is also the sender's email for a clean appearance).
    * Crucially, it uses the `Bcc` field (`GMAIL_RECIPIENTS`) to send the email to all actual recipients, keeping their addresses hidden from each other for privacy.

* **Sending Mechanism**: Encodes the constructed email message into a base64 URL-safe string and sends it using the Gmail API's `users().messages().send` method.

## Assets (`assets/`)

This directory is intended to store any static files used by the newsletter, such as:

* Templates for the newsletter layout.

* Images or logos included in the digest, including the main project logo located at `assets/digest.png`.

* Other resources that enhance the appearance or content of the newsletter.

## Usage

Once configured, the workflow will automatically run daily at the scheduled time. You can also trigger it manually:

1.  Go to the "Actions" tab in your GitHub repository.

2.  Select the "Daily Cybersecurity Digest" workflow from the left sidebar.

3.  Click the "Run workflow" dropdown on the right and then click the "Run workflow" button.

You should expect to receive the daily cybersecurity digest in your configured Telegram chat and email inbox at the specified times.

## Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please:

1.  Open an issue to discuss your ideas.

2.  Fork the repository.

3.  Create a new branch (`git checkout -b feature/your-feature-name`).

4.  Make your changes and commit them (`git commit -m 'Add new feature'`).

5.  Push to your branch (`git push origin feature/your-feature-name`).

6.  Open a pull request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Contact

If you have any questions or need further assistance, please open an issue in this repository.
