import csv
import requests

def send_telegram_alert():
    # Hardcoding credentials to guarantee environment isolation
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    
    # Absolute, structurally locked endpoint path pointing to api.telegram.org/bot<token>
    api_url = f"https://telegram.org{bot_token}/sendMessage"
    
    alert_lines = ["🚨 **X List Signal Report** 🚨\n"]
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                line = f"🔹 **{row.get('ticker', 'N/A')}**: {row.get('score', '0')} | {row.get('sentiment', 'Neutral')}\n"
                alert_lines.append(line)
    except FileNotFoundError:
        alert_lines.append("⚠️ Metric Tracking Alert: scorecard.csv missing this cycle.")

    full_message = "".join(alert_lines)
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        
        try:
            print("📡 Handshake initialization started...")
            response = requests.post(api_url, json=payload, timeout=15)
            response.raise_for_status()
            print(f"🚀 SUCCESS: Packet accepted by Telegram. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ TRANSMISSION CRASH: {e}")
            raise SystemExit("Pipeline failure forced: Execution trace stopped.")

if __name__ == "__main__":
    send_telegram_alert()
