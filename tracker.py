import csv
import os

# 1. Tier Weight Configuration
TIER_1_ACCOUNTS = ['financialjuice', 'GlobalMacroZen', 'YCCMacro', 'ExanteData', 'Econimica']

# 2. Enhanced Keyword Maps (Direction-Aware)
GROWTH_EXPANSION = ['pmi expansion', 'gdp beats', 'growth surges', 'hiring booms', 'strong retail']
GROWTH_CONTRACTION = ['pmi contraction', 'recession risk', 'growth crashes', 'layoffs', 'unemployment spikes']

INFLATION_HAWKISH = ['cpi spikes', 'inflation rises', 'pce acceleration', 'rate hike', 'fed hikes', 'hawkish']
INFLATION_DOVISH = ['cpi cooling', 'inflation drops', 'pce slowdown', 'disinflation', 'deflationary']

LIQUIDITY_EXPANSION = ['rate cut', 'fed cuts', 'qe', 'liquidity injection', 'dovish pivot', 'bailout']
LIQUIDITY_CONTRACTION = ['qt', 'balance sheet taper', 'liquidity drain', 'tightening conditions']

# Initialize Aggregate Vector Scores
growth_vector = 0
inflation_vector = 0
liquidity_vector = 0
total_tweets = 0

print("Executing institutional quantamental scoring logic...")

if os.path.exists("tracker.csv"):
    with open("tracker.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            account = row.get("Account", "")
            text = (row.get("Tweet_Text") or row.get("tweet_text") or "").lower()
            if not text:
                continue
                
            total_tweets += 1
            
            # Apply Tier 1 (3x) or Tier 2 (1x) Multiplier Weight
            weight = 3 if account in TIER_1_ACCOUNTS else 1
            
            # Score Growth Vector
            for kw in GROWTH_EXPANSION:
                if kw in text: growth_vector += (1 * weight)
            for kw in GROWTH_CONTRACTION:
                if kw in text: growth_vector -= (1 * weight)
                
            # Score Inflation Vector
            for kw in INFLATION_HAWKISH:
                if kw in text: inflation_vector += (1 * weight)
            for kw in INFLATION_DOVISH:
                if kw in text: inflation_vector -= (1 * weight)
                
            # Score Liquidity Vector
            for kw in LIQUIDITY_EXPANSION:
                if kw in text: liquidity_vector += (1 * weight)
            for kw in LIQUIDITY_CONTRACTION:
                if kw in text: liquidity_vector -= (1 * weight)

# 3. Structural Matrix Regime Clash Analysis
overall_bias = "NEUTRAL (Wait for Data)"

# Regime 1: Bad News is Good News (Growth down but Liquidity printing)
if growth_vector < -3 and liquidity_vector > 3:
    overall_bias = "⚡ RISK-ON BUY (Central Bank Bailout / Asset Expansion)"

# Regime 2: Hard Stagflation (Growth down, Inflation spiking, Liquidity draining)
elif growth_vector < -3 and inflation_vector > 3 and liquidity_vector <= 0:
    overall_bias = "🚨 RISK-OFF SELL (Stagflation Crisis / Asset Contraction)"

# Regime 3: Goldilocks (Growth solid, Inflation dropping or steady, Liquidity stable)
elif growth_vector > 3 and inflation_vector <= 0 and liquidity_vector >= 0:
    overall_bias = "📈 RISK-ON BUY (Goldilocks Expansion / Equity Outperformance)"

# Fallback Linear Condition if no matrix clash triggers
elif (growth_vector + liquidity_vector - inflation_vector) > 5:
    overall_bias = "BUY BIAS (Positive Linear Vector Matrix)"
elif (growth_vector + liquidity_vector - inflation_vector) < -5:
    overall_bias = "SELL BIAS (Negative Linear Vector Matrix)"

print(f"Scoring Complete. Outputting Matrix Bias: {overall_bias}")

# 4. Generate the uncollapsed granular scorecard rows
with open("scorecard.csv", mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric_Type", "Value"])
    writer.writerow(["Processed_Feeds", total_tweets])
    writer.writerow(["Growth_Vector", growth_vector])
    writer.writerow(["Inflation_Vector", inflation_vector])
    writer.writerow(["Liquidity_Vector", liquidity_vector])
    writer.writerow(["Calculated_Bias", overall_bias])
