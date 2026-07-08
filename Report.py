import csv
import requests

def send_telegram_alert():
    # Credentials
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    
    # Target Endpoint
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    alert_lines = ["🚨 **X List Signal Report** 🚨\n"]
    
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract exact matching column headers from scorecard.csv
                handle = row.get("Analyst_Handle", "Unknown")
                forecasts = row.get("Total_Forecasts", "0")
                active = row.get("Active_Open", "0")
                win_rate = row.get("Win_Rate_%", "0.0%")
                status = row.get("Status_Flag", "N/A")
                
                # Format a scannable message line for each analyst row
                line = f"👤 **{handle}** | Actives: {active} | Win Rate: {win_rate} | {status}\n"
                alert_lines.append(line)
                
    except FileNotFoundError:
        alert_lines.append("⚠️ Metric Tracking Alert: scorecard.csv missing this cycle.")

    full_message = "\n".join(alert_lines)
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        
        try:
            print("Handshake initialization started...")
            response = requests.post(api_url, json=payload, timeout=15)
            response.raise_for_status()
            print(f"SUCCESS: Packet accepted by Telegram. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ TRANSMISSION CRASH: {e}")
            raise SystemExit("Pipeline failure forced: Execution trace stopped.")

if __name__ == "__main__":
    send_telegram_alert()
