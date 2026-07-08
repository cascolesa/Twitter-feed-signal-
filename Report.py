import csv
import requests

def escape_html(text):
    """Safely escapes HTML characters to prevent Telegram API parsing errors."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_telegram_alert():
    # Credentials
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    
    # Target Endpoint
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Base header initialized with valid HTML tags
    alert_lines = ["<b>🚨 X List Signal Report 🚨</b>\n"]
    
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract and HTML-escape every parsed column variable
                handle = escape_html(row.get("Analyst_Handle", "Unknown"))
                forecasts = escape_html(row.get("Total_Forecasts", "0"))
                active = escape_html(row.get("Active_Open", "0"))
                win_rate = escape_html(row.get("Win_Rate_%", "0.0%"))
                status = escape_html(row.get("Status_Flag", "N/A"))
                
                # Format a scannable message line using HTML tags (<b> and <code>)
                line = f"👤 <b>{handle}</b> | Actives: {active} | Win Rate: {win_rate} | <code>{status}</code>"
                alert_lines.append(line)
                
    except FileNotFoundError:
        alert_lines.append("⚠️ <b>Metric Tracking Alert:</b> <code>scorecard.csv</code> missing this cycle.")

    # Join with newlines
    full_message = "\n".join(alert_lines)
    
    # Safety slice: Chunk payload at 4000 characters to keep it well below Telegram's limit
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML"  # Shifted parameter to explicitly parse HTML tags
        }
        
        try:
            print("Handshake initialization started...")
            # Using data= instead of json= ensures reliable application/x-www-form-urlencoded parsing by Telegram
            response = requests.post(api_url, data=payload, timeout=15)
            response.raise_for_status()
            print(f"SUCCESS: Packet accepted by Telegram. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # Catch detailed server text feedback for better troubleshooting visibility
            error_details = response.text if 'response' in locals() else ""
            print(f"❌ TRANSMISSION CRASH: {e} | Details: {error_details}")
            raise SystemExit("Pipeline failure forced: Execution trace stopped.")

if __name__ == "__main__":
    send_telegram_alert()
