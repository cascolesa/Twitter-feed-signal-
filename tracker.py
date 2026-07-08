import os
import csv
import re

def analyze_macro_sentiment(text):
    text_lower = text.lower()
    score = 0.0
    bullish = ["spiking", "long", "deficit", "growth", "higher", "hawkish", "accumulate"]
    bearish = ["stalls", "weak", "outflows", "compression", "dropping", "dovish", "liquidate"]
    for w in bullish:
        if w in text_lower: score += 0.35
    for w in bearish:
        if w in text_lower: score -= 0.35
    return max(min(score, 1.0), -1.0)

def route_and_filter_data(input_csv="tracker.csv", output_csv="scorecard.csv"):
    if not os.path.exists(input_csv):
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=["Analyst_Handle", "Total_Forecasts", "Active_Open", "Win_Rate_%", "Status_Flag"]).writeheader()
        return

    # Categories tracking core macro streams
    macro_routes = {
        "forex": ["dxy", "usd", "eur", "jpy", "gbp", "yields", "fed", "inflation", "cpi"],
        "commodities": ["crude", "oil", "brent", "gold", "xau", "copper", "gas", "wti", "gazprom"],
        "crypto": ["btc", "eth", "sol", "liquidity", "crypto", "stablecoin", "bitcoin"],
        "stocks_and_indices": ["spy", "spx", "ndx", "stocks", "earnings", "nasdaq", "vix", "equities", "s&p", "russell"]
    }
    
    analyst_metrics = {}

    with open(input_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # FIXED: Targeting image schema headers
            tweet_text = row.get("Tweet_Text", "")
            raw_username = row.get("Account", "").strip() or "Unknown_Analyst"
            
            # FIX: Clean out retweets, mentions, and common trading platform naming artifacts
            # e.g., transforms "RT @KoyfinCharts" -> "KoyfinCharts"
            cleaned_username = re.sub(r'^(RT\s+)?@', '', raw_username).strip()
            
            # Clean HTML character mutations from social feed pulls
            cleaned_text = tweet_text.replace("&amp;", "&").lower()
            
            assigned_category = "unclassified"
            for category, keywords in macro_routes.items():
                if any(k in cleaned_text for k in keywords):
                    assigned_category = category
                    break
            
            # CATCH-ALL ACTION: Routes rows that fail all primary criteria lists
            if assigned_category == "unclassified":
                assigned_category = "macro_unclassified"
                
            if cleaned_username not in analyst_metrics:
                analyst_metrics[cleaned_username] = {"Total_Forecasts": 0, "Active_Open": 0}
            
            analyst_metrics[cleaned_username]["Total_Forecasts"] += 1
            analyst_metrics[cleaned_username]["Active_Open"] += 1

    processed_rows = []
    for username, data in analyst_metrics.items():
        processed_rows.append({
            "Analyst_Handle": username,
            "Total_Forecasts": str(data["Total_Forecasts"]),
            "Active_Open": str(data["Active_Open"]),
            "Win_Rate_%": "0.0%",
            "Status_Flag": "UNDER_REVIEW"
        })

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Analyst_Handle", "Total_Forecasts", "Active_Open", "Win_Rate_%", "Status_Flag"])
        writer.writeheader()
        writer.writerows(processed_rows)

if __name__ == "__main__": 
    route_and_filter_data()
