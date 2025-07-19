html_digest = f"""
<html>
  <head>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
  </head>
  <body style="margin:0; padding:0; background:#0f0f0f; font-family:'Inter', sans-serif; color:#ffffff;">
    <div style="max-width:640px; margin:40px auto; background:#121212; border-radius:16px; overflow:hidden; box-shadow:0 8px 24px rgba(0,0,0,0.3);">

      <!-- Header with Logo -->
      <div style="background:#00ffe0; color:#000000; padding:24px 32px; display:flex; align-items:center; gap:16px;">
        <img src="https://raw.githubusercontent.com/throwaway666-ui/Telegram-Research-Channel/main/assets/logo.png" alt="Logo" style="height:48px; border-radius:8px;" />
        <div>
          <h1 style="margin:0; font-size:28px; font-weight:700; font-family:'Space Grotesk', sans-serif; letter-spacing:-0.5px;">
            Cybersecurity Digest
          </h1>
          <p style="margin:4px 0 0; font-size:14px; font-weight:500; font-family:'Inter', sans-serif;">{today_str}</p>
        </div>
      </div>

      <!-- Cyber News -->
      <div style="background:#1e1e1e; padding:32px;">
        <h2 style="color:#ffffff; font-size:20px; font-weight:600; font-family:'Space Grotesk', sans-serif;">
          📰 Today’s Cybersecurity Headlines
        </h2>
        {html_items}
      </div>

      <!-- Footer -->
      <div style="text-align:center; padding:20px 0; font-size:12px; color:#888888; font-family:'Inter', sans-serif;">
        Stay secure. This digest was sent by your automated cybersecurity agent.<br>
        <span style="color:#555;">© {today_str[:4]} Cyber Digest Bot</span>
      </div>

    </div>
  </body>
</html>
"""

