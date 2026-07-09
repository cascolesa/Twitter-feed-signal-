import os
import csv
import json
import urllib.request
import urllib.parse
import urllib.error
import logging

# Configure logging for GitHub Actions runner stdout
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Pull Telegram credentials securely from the environment context 
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Fixed Telegram Chat ID extracted from your system blueprint matrix
TELEGRAM_CHAT_ID = "1941531363"

def escape_html_tags(text):
    """
    Escapes loose tags inside raw text bytes to prevent Telegram's 
    HTML parser from throwing 400 Bad Request processing anomalies.
    """
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_macro_dashboard_html():
    """
    Reads data states out of tracker.csv and scorecard.csv to construct
    a structured, scannable HTML quantitative intelligence report.
    """
    tracker_file = "tracker.csv"
    scorecard_file = "scorecard.csv"
    
    html_body = "<b>📊 SYSTEMATIC GLOBAL MACRO SCORECARD</b>\n"
    html_body += "====================================\n\n"
    
    # 1. Attempt to inject processed factor matrices out of scorecard.csv
    if os.path.exists(scorecard_file):
        html_body += "<b>📈 QUANTAMENTAL FACTOR MATRICES:</b>\n"
        try:
            with open(scorecard_file, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or len(row) < 2:
                        continue
                    # Skip printing raw column title array labels directly
                    if row[0] == "Metric_Type":
                        continue
                    metric = escape_html_tags(row[0])
                    val = escape_html_tags(row[1])
                    html_body += f"• {metric.replace('_', ' ')}: <code>{val}</code>\n"
            html_body += "\n"
        except Exception as csv_error:
            html_body += f"<i>[Warning] Failed to parse scorecard matrix: {str(csv_error)}</i>\n\n"
    else:
        html_body += "<b>⚠️ FACTOR MATRIX STATE:</b>\n<code>No matrix file found. Fallback mode active.</code>\n\n"

    # 2. Extract feed data tracking history from tracker.csv
    html_body += "<b>📡 LIVE RAW INGESTION FEED TRACKER:</b>\n"
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                records_processed = 0
                
                for row in reader:
                    # Limiting message scope to prevent breaching Telegram's 4096 character size restriction
                    if records_processed >= 8:
                        html_body += "\n<i>[Truncated: Maximum payload threshold reached]</i>\n"
                        break
                        
                    handle = escape_html_tags(row.get('handle', 'UNKNOWN'))
                    raw_description = row.get('description', '')
                    pub_date = escape_html_tags(row.get('pubDate', ''))
                    
                    if raw_description:
                        # Slice the raw payload first to prevent splitting mid-HTML escaped character entity
                        truncated_raw = raw_description[:120] + "..." if len(raw_description) > 120 else raw_description
                        description = escape_html_tags(truncated_raw)
                        
                        html_body += f"<b>@{handle}</b> | <i>{pub_date}</i>\n"
                        html_body += f"└ <code>{description}</code>\n\n"
                        records_processed += 1
                        
                if records_processed == 0:
                    html_body += "<i>No raw items captured during this cycle window.</i>\n"
        except Exception as csv_error:
            html_body += f"<i>[Warning] Failed to process tracker stream: {str(csv_error)}</i>\n"
    else:
        html_body += "<i>tracker.csv input ledger missing from workspace memory.</i>\n"
        
    return html_body

def dispatch_telegram_alert(html_payload):
    """
    Pushes the compiled quantitative thesis directly to Telegram standard API routes 
    using native urllib POST handling and a strict 15-second network timeout.
    """
    if not TELEGRAM_BOT_TOKEN:
        logging.critical("[ABORT] TELEGRAM_BOT_TOKEN tracking key missing from runtime environment variables.")
        return False
        
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Configure precise request attributes specifying explicit HTML parsing modes
    payload_data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": html_payload,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true"
    }
    
    try:
        # Encode dictionaries directly to valid system query arrays
        encoded_bytes = urllib.parse.urlencode(payload_data).encode("utf-8")
        req = urllib.request.Request(api_url, data=encoded_bytes, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        logging.info(f"Dispatching quantitative reporting matrix to Chat ID: {TELEGRAM_CHAT_ID}...")
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("ok"):
                logging.info("✅ Macro dashboard successfully dispatched to Telegram channels.")
                return True
            else:
                logging.error(f"❌ Telegram API rejected transaction message payload: {result}")
                return False
                
    except urllib.error.HTTPError as http_err:
        logging.error(f"❌ HTTP Error encountered during dispatch: {http_err.code} - {http_err.read().decode('utf-8')}")
        return False
    except Exception as general_err:
        logging.error(f"❌ Structural networking exception triggered inside Report module: {str(general_err)}")
        return False

def main():
    logging.info("=== GENERATING DOWNSTREAM REPORT METRIC ARRAYS ===")
    compiled_report = generate_macro_dashboard_html()
    dispatch_telegram_alert(compiled_report)

if __name__ == "__main__":
    main()
