import csv
import requests

def escape_html(text): 
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_telegram_alert():
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    
    # FIXED: Correct, fully-formed Telegram endpoint URL path
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    alert_lines = ["<b>🚨 X List Signal Report 🚨</b>\n"]
    row_counter = 0
    
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_counter += 1
                handle = escape_html(row.get("Analyst_Handle", "Unknown"))
                active = escape_html(row.get("Active_Open", "0"))
                win_rate = escape_html(row.get("Win_Rate_%", "0.0%"))
                status = escape_html(row.get("Status_Flag", "N/A"))
                alert_lines.append(f"👤 <b>{handle}</b> | Actives: {active} | Win Rate: {win_rate} | <code>{status}</code>")
    except FileNotFoundError: 
        pass
        
    if row_counter == 0: 
        alert_lines.append("<i>(No active analyst metrics found in this update package)</i>")
        
    full_message = "\n".join(alert_lines)
    payload_chunks = [full_message[i:i+4000] for i in range(0, len(full_message), 4000)]
    
    for chunk in payload_chunks:
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"}
        requests.post(api_url, data=payload, timeout=15).raise_for_status()

if __name__ == "__main__": 
    send_telegram_alert()
