import os
import csv
import requests

def aggregate_scores(file_path="scorecard.csv"):
    """Groups historical sentiment values by asset category to find the net tone."""
    summary = {"forex": [], "commodities": [], "crypto": [], "stocks_and_indices": []}
    if not os.path.exists(file_path): return summary
    with open(file_path, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = row.get("category")
            if cat in summary: summary[cat].append(float(row.get("score", 0)))
    return summary

def construct_and_send_telegram():
    """Generates the macro text layout and delivers it directly to your Telegram."""
    data = aggregate_scores()
    body = "=== AUTOMATED GLOBAL MACRO REPORT ===\n\n"
    
    for asset, scores in data.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        bias = "BULLISH BIAS" if avg > 0.15 else ("BEARISH BIAS" if avg < -0.15 else "NEUTRAL RANGE")
        body += f"[{asset.upper()}]\n - Sentiment Index: {avg:.2f}\n - Forward Outlook: {bias}\n - History Samples: {len(scores)}\n\n"

    # Securely retrieve system environment keys from GitHub
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print(f"Configuration missing. Fallback Report View:\n{body}")
        return

    url = f"https://telegram.org{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": body}
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Macro brief successfully delivered to Telegram!")
    else:
        print(f"Transmission failed: {response.text}")

if __name__ == "__main__":
    construct_and_send_telegram()
