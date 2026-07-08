import csv
import requests

def send_telegram_alert():
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    api_url = f"https://telegram.org{bot_token}/sendMessage"
    
    # Build payload from scorecard
    alert_lines = ["🚨 **X List Signal Report** 🚨\n"]
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Format compact, scannable lines for mobile UI
                line = f"🔹 **{row.get('ticker', 'N/A')}**: {row.get('score', '0')} | {row.get('sentiment', 'Neutral')}\n"
                alert_lines.append(line)
    except FileNotFoundError:
        alert_lines.append("⚠️ Critical Error: scorecard.csv not found.")

    # Chunk payloads to guarantee visibility under 4096-char ceiling
    full_message = "".join(alert_lines)
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
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
