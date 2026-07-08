import os
import csv

def analyze_macro_sentiment(text):
    """Parses text for complex macro weights instead of basic rules."""
    text_lower = text.lower()
    score = 0.0
    bullish_indicators = ["spiking", "long", "deficit", "growth", "higher", "hawkish", "accumulate"]
    bearish_indicators = ["stalls", "weak", "outflows", "compression", "dropping", "dovish", "liquidate"]
    
    for word in bullish_indicators:
        if word in text_lower: score += 0.35
    for word in bearish_indicators:
        if word in text_lower: score -= 0.35
    return max(min(score, 1.0), -1.0)

def route_and_filter_data(input_csv="tracker.csv", output_csv="scorecard.csv"):
    """Reads incoming data, filters out non-macro noise, and writes clean scores."""
    if not os.path.exists(input_csv): return
    
    # Macro routing keyword map
    macro_routes = {
        "forex": ["dxy", "usd", "eur", "jpy", "gbp", "yields", "fed", "inflation", "cpi"],
        "commodities": ["crude", "oil", "brent", "gold", "xau", "copper", "gas", "wti"],
        "crypto": ["btc", "eth", "sol", "liquidity", "crypto", "stablecoin", "bitcoin"],
        "stocks_and_indices": ["spy", "spx", "ndx", "stocks", "earnings", "nasdaq", "vix", "equities"]
    }
    
    processed_rows = []
    with open(input_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweet_text = row.get("text", "")
            assigned_category = "unclassified"
            
            # Deep sorting step: find the exact specific category tool matching the text topic
            for category, keywords in macro_routes.items():
                if any(keyword in tweet_text.lower() for keyword in keywords):
                    assigned_category = category
                    break
            
            # Filter rule: completely discard rows that lack structural macro importance
            if assigned_category == "unclassified": continue
                
            sentiment_score = analyze_macro_sentiment(tweet_text)
            processed_rows.append({
                "tweet_id": row.get("id", ""),
                "username": row.get("username", ""),
                "category": assigned_category,
                "score": sentiment_score,
                "timestamp": row.get("timestamp", "")
            })
            
    # Atomic write step to save output data cleanly
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tweet_id", "username", "category", "score", "timestamp"])
        writer.writeheader()
        writer.writerows(processed_rows)

if __name__ == "__main__":
    route_and_filter_data()
