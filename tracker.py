import os
import csv
import re

def route_and_filter_data(input_csv="tracker.csv", output_csv="scorecard.csv"):
    if not os.path.exists(input_csv):
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            # Added Asset_Class column to header structure
            csv.DictWriter(f, fieldnames=["Analyst_Handle", "Asset_Class", "Total_Forecasts", "Active_Open", "Win_Rate_%", "Status_Flag"]).writeheader()
        return

    macro_routes = {
        "forex": ["dxy", "usd", "eur", "jpy", "gbp", "yields", "fed", "inflation", "cpi"],
        "commodities": ["crude", "oil", "brent", "gold", "xau", "copper", "gas", "wti", "gazprom"],
        "crypto": ["btc", "eth", "sol", "liquidity", "crypto", "stablecoin", "bitcoin"],
        "stocks_and_indices": ["spy", "spx", "ndx", "stocks", "earnings", "nasdaq", "vix", "equities", "s&p", "russell"]
    }
    
    # Tracking dictionary grouped by (analyst, category) combo
    analyst_metrics = {}

    with open(input_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweet_text = row.get("Tweet_Text", "") or ""
            raw_username = row.get("Account", "").strip() or "Unknown_Analyst"
            
            cleaned_username = re.sub(r'^(RT\s+)?@', '', raw_username).strip()
            cleaned_text = tweet_text.replace("&amp;", "&").lower()
            
            assigned_category = "unclassified"
            for category, keywords in macro_routes.items():
                if any(k in cleaned_text for k in keywords):
                    assigned_category = category
                    break
            
            if assigned_category == "unclassified":
                assigned_category = "macro_unclassified"
                
            # Group keys by both username AND their asset class
            metric_key = (cleaned_username, assigned_category)
                
            if metric_key not in analyst_metrics:
                analyst_metrics[metric_key] = {"Total_Forecasts": 0, "Active_Open": 0}
            
            analyst_metrics[metric_key]["Total_Forecasts"] += 1
            analyst_metrics[metric_key]["Active_Open"] += 1

    processed_rows = []
    for (username, category), data in analyst_metrics.items():
        processed_rows.append({
            "Analyst_Handle": username,
            "Asset_Class": category.upper(),  # Saves fundamental context flag
            "Total_Forecasts": str(data["Total_Forecasts"]),
            "Active_Open": str(data["Active_Open"]),
            "Win_Rate_%": "0.0%",
            "Status_Flag": "UNDER_REVIEW"
        })

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        # File headers updated to match data generation metrics
        writer = csv.DictWriter(f, fieldnames=["Analyst_Handle", "Asset_Class", "Total_Forecasts", "Active_Open", "Win_Rate_%", "Status_Flag"])
        writer.writeheader()
        writer.writerows(processed_rows)

if __name__ == "__main__": 
    route_and_filter_data()
