import csv
import os
import requests

def send_telegram_alert():
    # 1. Pull the exact keys exposed by main.yml
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    # 2. Strict validation to isolate exact environment failures
    if not bot_token:
        print("❌ CRITICAL SCRIPT ERROR: 'TELEGRAM_BOT_TOKEN' environment key returned Empty/None.")
        return
        
    if not chat_id:
        print("❌ CRITICAL SCRIPT ERROR: 'TELEGRAM_CHAT_ID' environment key returned Empty/None.")
        return

    # Stripping hidden carriage returns or whitespace that might break parsing
    bot_token = str(bot_token).strip()
    chat_id = str(chat_id).strip()

    # 3. Explicitly hardcode the exact, unalterable API URL format
    # Notice the presence of api. and /bot explicitly structured.
    api_url = f"https://telegram.org{bot_token}/sendMessage"
    
    alert_lines = ["🚨 **X List Signal Report** 🚨\n"]
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                line = f"🔹 **{row.get('ticker', 'N/A')}**: {row.get('score', '0')} | {row.get('sentiment', 'Neutral')}\n"
                alert_lines.append(line)
    except FileNotFoundError:
        alert_lines.append("⚠️ System Metric Alert: scorecard.csv was not generated during this cycle.")

    full_message = "".join(alert_lines)
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        
        try:
            print(f"📡 Initiating transmission handshake sequence...")
            response = requests.post(api_url, json=payload, timeout=12)
            response.raise_for_status()
            print(f"🚀 SUCCESS: Message block delivered. Server Response Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # Force the step to explicitly fail if the network packet drops
            print(f"❌ TRANSMISSION FAILED: {e}")
            if 'response' in locals() and response is not None:
                print(f"ℹ️ Core Telegram Output: {response.text}")
            raise SystemExit("Pipeline stopped: Handshake validation failure encountered.")

if __name__ == "__main__":
    send_telegram_alert()
