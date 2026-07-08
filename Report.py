import csv
import requests

def send_telegram_alert():
    # Hardcoding your verified working credentials directly to eliminate secret-parsing bugs
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    
    # Absolute, unalterable base URL string structure
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
            print(f"📡 Initiating direct transmission handshake sequence to api.telegram.org...")
            response = requests.post(api_url, json=payload, timeout=12)
            response.raise_for_status()
            print(f"🚀 SUCCESS: Message block delivered. Server Response Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ TRANSMISSION FAILED: {e}")
            raise SystemExit("Pipeline stopped: Network handshake validation failure.")

if __name__ == "__main__":
    send_telegram_alert()
