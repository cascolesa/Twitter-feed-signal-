import csv
import os
import requests

def send_telegram_alert():
    # Fetch secrets directly from the GitHub runner environment
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    # Fail-safe check if secrets are missing from the workflow environment
    if not bot_token or not chat_id:
        print("❌ Critical Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment.")
        return

    # Standard clean Telegram Base URL layout
    api_url = f"https://telegram.org{bot_token}/sendMessage"
    
    alert_lines = ["🚨 **X List Signal Report** 🚨\n"]
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                line = f"🔹 **{row.get('ticker', 'N/A')}**: {row.get('score', '0')} | {row.get('sentiment', 'Neutral')}\n"
                alert_lines.append(line)
    except FileNotFoundError:
        alert_lines.append("⚠️ Critical Error: scorecard.csv not found.")

    full_message = "".join(alert_lines)
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        
        response = None 
        try:
            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"Transmission successful. HTTP Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Network Handshake Failed: {e}")
            if response is not None:
                print(f"Telegram Server Response: {response.text}")

if __name__ == "__main__":
    send_telegram_alert()
