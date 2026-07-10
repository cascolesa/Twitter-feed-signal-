import os
import re
import json
import math
import urllib.request

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def calculate_cross_asset_statistics(current_matrix):
    """Calculates session-wide mean and standard deviation across all scanned assets."""
    gaps = [metrics["structural_divergence_gap"] for metrics in current_matrix.values()]
    
    if len(gaps) < 2:
        return 0.0, 1.0
        
    mean = sum(gaps) / len(gaps)
    variance = sum((x - mean) ** 2 for x in gaps) / len(gaps)
    std_dev = math.sqrt(variance)
    
    # Prevent division by zero if all asset gaps are identical
    if std_dev == 0.0:
        std_dev = 0.1
        
    return mean, std_dev

def dispatch_telegram_alert(message):
    """Routes quantitative signals directly to the Telegram API channel."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Notification skipped: Missing environmental credentials.")
        return
        
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() == 200:
                print("Signal successfully routed to Telegram.")
    except Exception as e:
        print(f"Telegram routing execution failure: {e}")

def process_and_evaluate_forecasts():
    """Applies cross-asset statistical outlier matrices to discover macro regime extremes."""
    if not os.path.exists("final_sentiment_matrix.json"):
        print("Error: final_sentiment_matrix.json not found.")
        return
        
    with open("final_sentiment_matrix.json", "r", encoding="utf-8") as f:
        current_matrix = json.load(f)
        
    # Calculate global session metrics across the asset universe
    session_mean, session_std = calculate_cross_asset_statistics(current_matrix)
    
    for asset, metrics in current_matrix.items():
        gap = metrics["structural_divergence_gap"]
        
        # Determine relative Z-Score against current global market environment
        z_score = (gap - session_mean) / session_std
        
        # Institutional Outlier Boundary: Trigger on 1.2+ Sigma variations
        if abs(z_score) >= 1.2:
            bias = "BUY / ACCUMULATE" if z_score > 0 else "SELL / DISTRIBUTE"
            regime = "STRUCTURAL BOTTOM" if z_score > 0 else "STRUCTURAL TOP"
            
            # Clean, Professional Summary Text Format
            alert_msg = (
                f"**QUANT MACRO ENGINE | POSITION ALIGNMENT REPORT**\n\n"
                f"**Asset Class:** {asset}\n"
                f"**Market Bias:** {bias}\n"
                f"**Regime Detection:** {regime}\n\n"
                f"**Core Quantitative Vectors:**\n"
                f"The structural divergence gap for {asset} currently measures {gap:+.4f}. "
                f"Evaluated against the broader macro asset classes, this reading represents a "
                f"statistical deviation of {z_score:+.2f} standard deviations from the session mean ({session_mean:+.4f}).\n\n"
                f"**Strategic Assessment:**\n"
                f"Hard macroeconomic data and soft market expectations have entered a phase of critical displacement. "
                f"This positioning highlights an asymmetric multi-week macro trend reversal opportunity. Monitor entry structures accordingly."
            )
            dispatch_telegram_alert(alert_msg)

if __name__ == "__main__":
    process_and_evaluate_forecasts()
