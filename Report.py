import csv
import os
import requests

def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def load_sent_history(history_file="sent_signals.txt"):
    """Loads historical fingerprints to protect against alert redundancy."""
    if not os.path.exists(history_file):
        return set()
    with open(history_file, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def append_to_history(post_hash, history_file="sent_signals.txt"):
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(f"{post_hash}\n")

def compile_and_dispatch_signals():
    bot_token = "8827323413:AAHMJWvAvXvrlVGESkHmY-TLhfvFacy3AsI"
    chat_id = "1941531363"
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    sent_hashes = load_sent_history()
    new_dispatches_count = 0
    
    category_emojis = {"FOREX": "💱", "STOCKS": "📈", "COMMODITIES": "🛢️", "CRYPTO": "🪙"}
    
    try:
        with open("scorecard.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                post_hash = row.get("Post_Hash", "")
                
                # Deduplication Filter: Completely blocks repeat processing runs
                if post_hash in sent_hashes:
                    continue
                
                analyst = escape_html(row.get("Analyst", "GENERIC"))
                asset = escape_html(row.get("Asset", "MACRO"))
                ticker = escape_html(row.get("Ticker", "GLOBAL"))
                bias = escape_html(row.get("Bias", "HOLD"))
                timestamp = escape_html(row.get("Timestamp", "N/A"))
                source_text = escape_html(row.get("Text", ""))
                
                # Check for triggering conditions
                theses = []
                if int(row.get("Growth", 0)) > 0: theses.append("Yield Curve Nowcasting Adjustment")
                if int(row.get("Inflation", 0)) > 0: theses.append("Regime-Shift Inflation Pressure")
                if int(row.get("Liquidity", 0)) > 0: theses.append("Systemic Central Bank Balance Sheet Move")
                if int(row.get("Supply_Shock", 0)) > 0: theses.append("Physical Inelastic Supply Disturbance")
                
                if not theses:
                    theses.append("Global Momentum Flow Alignment")
                    
                cmd_flag = "🟩 [VALID SYSTEMATIC BUY]" if bias == "BUY" else "🟥 [VALID SYSTEMATIC SELL]"
                emoji = category_emojis.get(asset, "🌐")
                
                # Formulate structural thesis dispatch card
                telegram_card = (
                    f"🏢 <b>QUANTAMENTAL MACRO EXECUTION SIGNAL</b>\n"
                    f"─────────────────────────\n"
                    f"📡 <b>Source:</b> @{analyst} | 🕒 <code>{timestamp}</code>\n"
                    f"{emoji} <b>Asset / Target:</b> <code>{ticker}</code> ({asset})\n"
                    f"⚡ <b>Action Assignment:</b> <b>{cmd_flag}</b>\n\n"
                    f"🔑 <b>Model Validation Triggers:</b>\n"
                    f"• " + "\n• ".join(theses) + f"\n\n"
                    f"📋 <b>Contextual Field Insights:</b>\n"
                    f"<i>\"{source_text}\"</i>\n"
                    f"─────────────────────────"
                )
                
                # Send out the signal payload
                payload = {"chat_id": chat_id, "text": telegram_card, "parse_mode": "HTML"}
                requests.post(api_url, data=payload, timeout=15).raise_for_status()
                
                # Permanently append fingerprint to state tracker
                append_to_history(post_hash)
                new_dispatches_count += 1
                
    except FileNotFoundError:
        print("Scorecard processing asset missing.")
        return

    if new_dispatches_count == 0:
        print("Execution run complete: No new underlying macro triggers parsed.")

if __name__ == "__main__":
    compile_and_dispatch_signals()
