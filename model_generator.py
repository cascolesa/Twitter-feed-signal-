import os
import re
import math
from datetime import datetime, timezone, timedelta

# Precise Asset Mapping Grid
ASSET_KEYWORDS = {
    "GOLD": [r"\bgold\b", r"\bxau\b", r"\bprecious metal\b"],
    "CRUDE_OIL": [r"\boil\b", r"\bcrude\b", r"\bwti\b", r"\bbrnt\b", r"\bmercuria\b"],
    "SPX_NAS": [r"\bspx\b", r"\bs&p\b", r"\bnasdaq\b", r"\bnas100\b", r"\bequities\b", r"\bwall street\b"],
    "FOREX_G10": [r"\busd\b", r"\beur\b", r"\bgbp\b", r"\bjpy\b", r"\baud\b", r"\bcad\b", r"\bchf\b", r"\bnzd\b"]
}

# Macro Metric Rule Grid
MACRO_KEYWORDS = [r"\bfed\b", r"\becb\b", r"\bboe\b", r"\boj\b", r"\brate\b", r"\binflation\b", r"\bcpi\b", r"\bgdp\b", r"\bhawkish\b", r"\bdovish\b"]

def get_dynamic_cutoff(now):
    """Calculates the dynamic lookback cut-off to prevent cross-quarter data contamination."""
    current_month = now.month
    current_year = now.year
    
    # Establish the absolute start of the current calendar quarter
    current_quarter = (current_month - 1) // 3 + 1
    q_start_month = (current_quarter - 1) * 3 + 1
    quarter_start_dt = datetime(current_year, q_start_month, 1, tzinfo=timezone.utc)
    
    # Identify Month 2 of any quarter (Feb, May, Aug, Nov)
    is_month_two = current_month in [2, 5, 8, 11]
    
    if is_month_two:
        days_diff = (now - quarter_start_dt).days
        if days_diff > 30:
            return now - timedelta(days=30)
            
    return quarter_start_dt

def calculate_time_decay(post_time, now, half_life_days=14.0):
    """Applies exponential time decay matrix based on an optimal 14-day positional half-life."""
    delta_days = (now - post_time).total_seconds() / 86400.0
    if delta_days < 0:
        delta_days = 0.0
    return math.pow(0.5, delta_days / half_life_days)

def categorize_and_tag_matrix():
    """Reads raw ingest text, processes time matrices, and outputs meta-tagged data rows."""
    if not os.path.exists("raw_ingest_matrix.txt"):
        print("Error: raw_ingest_matrix.txt not found.")
        return
        
    now = datetime.now(timezone.utc)
    cutoff_date = get_dynamic_cutoff(now)
    
    with open("raw_ingest_matrix.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    tagged_output = []

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        ts_match = re.search(r"^\[TIMESTAMP:([^\]]+)\]", line_clean)
        if not ts_match:
            continue
            
        try:
            post_time = datetime.fromisoformat(ts_match.group(1))
            if post_time.tzinfo is None:
                post_time = post_time.replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if post_time < cutoff_date:
            continue

        decay_weight = calculate_time_decay(post_time, now)
        body_text = re.sub(r"^\[TIMESTAMP:[^\]]+\]", "", line_clean).strip()
        body_lower = body_text.lower()

        matched_assets = []
        for asset, patterns in ASSET_KEYWORDS.items():
            if any(re.search(p, body_lower) for p in patterns):
                matched_assets.append(asset)
                
        if not matched_assets:
            continue

        is_numerical = any(char.isdigit() and "%" in body_lower for char in body_lower)
        is_macro = any(re.search(p, body_lower) for p in MACRO_KEYWORDS)

        if is_numerical and "[source:rss]" in body_lower:
            workflow_tag = "[MODEL:NUMERICAL_DELTA]"
        elif is_macro:
            workflow_tag = "[MODEL:CONTEXTUAL_LEXICON]"
        else:
            workflow_tag = "[MODEL:BIPOLAR_MOMENTUM]"

        asset_string = ",".join(matched_assets)
        tagged_output.append(f"{workflow_tag}[ASSETS:{asset_string}][TIME_DECAY:{decay_weight:.4f}] {body_text}")

    with open("tagged_model_matrix.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(tagged_output))
        
    print(f"Data processing complete. Active macro matrix lines remaining: {len(tagged_output)}")

if __name__ == "__main__":
    categorize_and_tag_matrix()
