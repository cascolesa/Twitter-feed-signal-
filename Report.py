import csv
import os
import requests

def escape_html(text):
    """Safely escapes HTML characters to prevent Telegram API parsing errors."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_telegram_alert():
    # Credentials
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    alert_lines = ["<b>🚨 X List Signal Report 🚨</b>\n"]
    row_counter = 0
    
    # Diagnostic Trace: Log current file parameters inside the CI environment
    if os.path.exists("scorecard.csv"):
        file_size = os.path.getsize("scorecard.csv")
        print(f"📋 DIAGNOSTIC: scorecard.csv found. Size: {file_size} bytes.")
    else:
        print("❌ DIAGNOSTIC ERROR: scorecard.csv is completely missing from workspace!")

    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            # Print raw data structure to log to catch case discrepancies or blank spaces
            raw_preview = f.read(300)
            print(f"📋 DIAGNOSTIC HEADER PREVIEW:\n{raw_preview}\n---")
            f.seek(0) # Reset tracking file pointer to index zero
            
            reader = csv.DictReader(f)
            for row in reader:
                row_counter += 1
                
                # Fetch row variables using strict fallbacks
                handle = escape_html(row.get("Analyst_Handle", "Unknown"))
                active = escape_html(row.get("Active_Open", "0"))
                win_rate = escape_html(row.get("Win_Rate_%", "0.0%"))
                status = escape_html(row.get("Status_Flag", "N/A"))
                
                # Construct clean HTML lines
                line = f"👤 <b>{handle}</b> | Actives: {active} | Win Rate: {win_rate} | <code>{status}</code>"
                alert_lines.append(line)
                
    except FileNotFoundError:
        alert_lines.append("⚠️ <b>Metric Tracking Alert:</b> <code>scorecard.csv</code> missing this cycle.")

    print(f"📋 DIAGNOSTIC: Successfully processed {row_counter} data rows from file.")

    # Fallback to catch empty processing cycles gracefully
    if row_counter == 0:
        alert_lines.append("<i>(No active analyst metrics found in this update package)</i>")

    full_message = "\n".join(alert_lines)
    
    # Print the absolute output text structure to the GitHub log to confirm content existence
    print(f"📋 FINAL PAYLOAD CONTENT PREVIEW:\n{full_message}\n---")
    
    # Safety slice: Chunk layout string safely
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML"
        }
        
        try:
            print("Handshake initialization started...")
            response = requests.post(api_url, data=payload, timeout=15)
            response.raise_for_status()
            print(f"SUCCESS: Packet accepted by Telegram. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            error_details = response.text if 'response' in locals() else ""
            print(f"❌ TRANSMISSION CRASH: {e} | Details: {error_details}")
            raise SystemExit("Pipeline failure forced: Execution trace stopped.")

if __name__ == "__main__":
    send_telegram_alert()
