import os
import csv
import urllib.request
import urllib.parse
import json

# 1. Telemetry & Routing Configuration (Fixed Variable Alignment)
TELEGRAM_BOT_TOKEN = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
TELEGRAM_CHAT_ID = "1941531363"

# 2. Extract Quantamental Matrix Metrics
metrics = {}
scorecard_path = "scorecard.csv"

if os.path.exists(scorecard_path):
    try:
        with open(scorecard_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row ["Metric_Type", "Value"]
            for row in reader:
                if len(row) == 2:
                    metrics[row[0]] = row[1]
    except Exception as e:
        print(f"Error parsing scorecard matrix data: {e}")

# Map variables with safe fallback defaults
processed_feeds = metrics.get("Processed_Feeds", "0")
growth_v = int(metrics.get("Growth_Vector", 0))
inflation_v = int(metrics.get("Inflation_Vector", 0))
liquidity_v = int(metrics.get("Liquidity_Vector", 0))
calculated_bias = metrics.get("Calculated_Bias", "NEUTRAL (Insufficient Data)")

# Format sub-vector status emojis visually based on value weights
g_emoji = "📈" if growth_v > 0 else ("📉" if growth_v < 0 else "⚪")
i_emoji = "🔥" if inflation_v > 0 else ("❄️" if inflation_v < 0 else "⚪")
l_emoji = "💧" if liquidity_v > 0 else ("🪨" if liquidity_v < 0 else "⚪")

# 3. Synthesize HTML Structural Trade Thesis Block
html_message = f"""<b>📊 SYSTEMATIC GLOBAL MACRO SCORECARD</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Analyzed Feed Volume:</b> {processed_feeds} posts combined.

<b>Regime Factor Matrix:</b>
• Growth Vector: {g_emoji} <code>{growth_v:+}</code>
• Inflation Vector: {i_emoji} <code>{inflation_v:+}</code>
• Liquidity Vector: {l_emoji} <code>{liquidity_v:+}</code>

<b>Directional Target Bias:</b>
🚨 <b>{calculated_bias}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━
<i>Engine execution: GitHub Actions Automated Run.</i>"""

# 4. Dispatch Secure HTML Payload via Native API Request
def send_telegram_broadcast(text):
    # FIXED: Replaced 'bot_token' with 'TELEGRAM_BOT_TOKEN' to resolve NameError
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode())
            if res_data.get("ok"):
                print("Macro dashboard dispatched successfully to Telegram.")
            else:
                print(f"Telegram API Warning: {res_data}")
    except Exception as e:
        print(f"Network Alert Dispatch Failure: {e}")

# Execute broadcast phase
send_telegram_broadcast(html_message)
