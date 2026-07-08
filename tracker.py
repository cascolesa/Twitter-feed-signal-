import os
import csv
import re
import hashlib

def generate_row_hash(username, text, timestamp):
    """Creates a unique deterministic fingerprint for each trade post to avoid duplication."""
    raw_string = f"{username}_{text}_{timestamp}"
    return hashlib.md5(raw_string.encode('utf-8')).hexdigest()

def evaluate_quantamental_factors(text):
    """
    Evaluates text against established academic macro risk models.
    Maps markers into Growth, Regime-Shift Inflation, Liquidity Vectors, and Supply Shocks.
    """
    text_lower = text.lower()
    factors = {"growth": 0, "inflation": 0, "liquidity": 0, "supply_shock": 0}
    
    # Growth & Macro Nowcasting Triggers
    if any(w in text_lower for w in ["yield", "growth", "fcf", "earnings", "output", "gdp", "nowcast", "revenue"]):
        factors["growth"] = 1
    # Inflation Regime Shifts
    if any(w in text_lower for w in ["inflation", "cpi", "pricing power", "wage", "commodity pricing", "core cpi"]):
        factors["inflation"] = 1
    # Central Bank Systemic Balance Sheet / Policy Liquidity
    if any(w in text_lower for w in ["fed", "hawkish", "dovish", "rate cut", "hike", "liquidity", "qt", "qe"]):
        factors["liquidity"] = 1
    # Flow of Funds / Structural Supply Inelasticity
    if any(w in text_lower for w in ["drone", "struck", "supply chain", "halt", "shutdown", "sanctions", "disruption", "pumping"]):
        factors["supply_shock"] = 1
        
    return factors

def isolate_ticker_and_bias(text):
    """Extracts explicit execution coordinates and directional weights."""
    text_lower = text.lower()
    
    asset_matrix = {
        "FOREX": (["dxy", "usd", "eur", "jpy", "gbp", "yields"], "USD_PAIRS"),
        "STOCKS": (["s&p", "spx", "nasdaq", "ndx", "russell", "spy", "equities"], "US_EQUITIES"),
        "COMMODITIES": (["gazprom", "crude", "oil", "brent", "gold", "xau", "gas"], "ENERGY_METALS"),
        "CRYPTO": (["btc", "eth", "sol", "bitcoin", "stablecoin"], "CRYPTO_ASSETS")
    }
    
    resolved_asset = "GLOBAL_MACRO"
    resolved_ticker = "CROSS_ASSET"
    
    for asset_class, (keywords, fallback_ticker) in asset_matrix.items():
        if any(k in text_lower for k in keywords):
            resolved_asset = asset_class
            if "s&p" in text_lower or "spx" in text_lower: resolved_ticker = "SPX"
            elif "nasdaq" in text_lower or "ndx" in text_lower: resolved_ticker = "NDX"
            elif "gazprom" in text_lower or "oil" in text_lower: resolved_ticker = "CRUDE_OIL"
            elif "dxy" in text_lower or "usd" in text_lower: resolved_ticker = "DXY"
            else: resolved_ticker = fallback_ticker
            break

    # Quant Sentiment Weight Assignment
    bull_weights = ["high", "spiking", "long", "expansion", "growth", "accumulate", "hawkish", "robust", "surplus"]
    bear_weights = ["weak", "stalls", "compression", "dropping", "liquidate", "struck", "dovish", "attack", "short"]
    
    net_weight = 0
    for w in bull_weights:
        if w in text_lower: net_weight += 1
    for w in bear_weights:
        if w in text_lower: net_weight -= 1
        
    execution_bias = "BUY" if net_weight >= 0 else "SELL"
    return resolved_asset, resolved_ticker, execution_bias

def pipeline_execution(input_csv="tracker.csv", output_csv="scorecard.csv"):
    if not os.path.exists(input_csv):
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=["Post_Hash", "Analyst", "Asset", "Ticker", "Bias", "Growth", "Inflation", "Liquidity", "Supply_Shock", "Timestamp", "Text"]).writeheader()
        return

    processed_signals = []
    
    with open(input_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Flexible dictionary fallback parsing to catch changing header snapshots
            raw_text = row.get("Tweet_Text") or row.get("text") or ""
            account = row.get("Account") or row.get("username") or "Unknown_Analyst"
            timestamp = row.get("Date_Logged") or row.get("timestamp") or "N/A"
            
            if not raw_text.strip():
                continue
                
            cleaned_username = re.sub(r'^(RT\s+)?@', '', account).strip()
            cleaned_text = raw_text.replace("&amp;", "&")
            
            # Form unique identity fingerprint to avoid execution redundancy
            row_hash = generate_row_hash(cleaned_username, cleaned_text, timestamp)
            factors = evaluate_quantamental_factors(cleaned_text)
            asset, ticker, bias = isolate_ticker_and_bias(cleaned_text)
            
            processed_signals.append({
                "Post_Hash": row_hash,
                "Analyst": cleaned_username,
                "Asset": asset,
                "Ticker": ticker,
                "Bias": bias,
                "Growth": str(factors["growth"]),
                "Inflation": str(factors["inflation"]),
                "Liquidity": str(factors["liquidity"]),
                "Supply_Shock": str(factors["supply_shock"]),
                "Timestamp": timestamp,
                "Text": cleaned_text.strip()
            })

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Post_Hash", "Analyst", "Asset", "Ticker", "Bias", "Growth", "Inflation", "Liquidity", "Supply_Shock", "Timestamp", "Text"])
        writer.writeheader()
        writer.writerows(processed_signals)

if __name__ == "__main__":
    pipeline_execution()
