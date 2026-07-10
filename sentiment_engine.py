import os
import re
import json

# Institutional Sentiment Weights Mapping (Standard Banking Lexicon Grid)
LEXICON_WEIGHTS = {
    # Central Bank & Macro Policy Tones
    "hawkish": 2.0, "tightening": 1.75, "hike": 1.5, "restrictive": 1.5, "elevated": 1.0,
    "dovish": -2.0, "easing": -1.75, "cut": -1.5, "accommodative": -1.5, "stimulus": -1.0,
    # Economic Growth Indicators
    "expansion": 1.5, "growth": 1.25, "acceleration": 1.25, "robust": 1.0, "rebound": 1.0,
    "recession": -2.0, "contraction": -1.75, "slowdown": -1.25, "weakness": -1.0, "slump": -1.5,
    # Price & Inflation Dynamics
    "inflationary": 1.5, "surge": 1.25, "hotter": 1.25, "spiral": 1.0,
    "deflationary": -1.5, "cooling": -1.25, "disinflation": -1.25, "subdued": -1.0,
    # General Market Bipolar Momentum
    "bullish": 1.0, "outperform": 1.25, "rally": 1.0, "demand": 0.75,
    "bearish": -1.0, "underperform": -1.25, "selloff": -1.5, "glut": -1.0
}

TARGET_ASSETS = ["GOLD", "CRUDE_OIL", "SPX_NAS", "FOREX_G10"]

def parse_tagged_line(line):
    """Extracts the parsing model, target assets, time decay, and data text from an entry."""
    model_match = re.search(r"^(\[MODEL:[^\]]+\])", line)
    assets_match = re.search(r"\[ASSETS:([^\]]+)\]", line)
    decay_match = re.search(r"\[TIME_DECAY:([^\]]+)\]", line)
    
    if not (model_match and assets_match and decay_match):
        return None
        
    model = model_match.group(1)
    assets = assets_match.group(1).split(",")
    decay = float(decay_match.group(1))
    
    # Strip the meta tags to isolate the raw body text
    body = re.sub(r"^\[MODEL:[^\]]+\]\[ASSETS:[^\]]+\]\[TIME_DECAY:[^\]]+\]", "", line).strip()
    return {"model": model, "assets": assets, "decay": decay, "body": body.lower()}

def evaluate_numerical_delta(text):
    """Scores statistical shifts by combining direction words with nearby numerical indicators."""
    score = 0.0
    # Search for percentage changes or point moves
    num_match = re.search(r"([-+]?\d*\.\d+|\d+)%", text)
    if num_match:
        # Determine directional vector context
        up_words = ["increase", "rise", "grew", "higher", "up", "surpassed", "above"]
        down_words = ["decrease", "fall", "dropped", "lower", "down", "missed", "below"]
        
        is_up = any(w in text for w in up_words)
        is_down = any(w in text for w in down_words)
        
        if is_up:
            score += 1.5
        elif is_down:
            score -= 1.5
    return score

def evaluate_lexicon_tone(text):
    """Scores soft text indicators by aggregating and normalizing institutional keyword weights."""
    score = 0.0
    matched_count = 0
    for word, weight in LEXICON_WEIGHTS.items():
        # Match using word boundaries to ensure precise parsing
        matches = len(re.findall(r'\b' + re.escape(word) + r'\b', text))
        if matches > 0:
            score += weight * matches
            matched_count += matches
            
    # Return raw text score normalized by keyword density if matches exist
    return score / matched_count if matched_count > 0 else score

def generate_sentiment_matrix():
    """Processes tagged text arrays and builds an institutional dual-layer sentiment scoring profile."""
    if not os.path.exists("tagged_model_matrix.txt"):
        print("Error: tagged_model_matrix.txt not found.")
        return

    # Initialise the score tracking matrix
    scoring_matrix = {asset: {"hard_data_vector": 0.0, "soft_sentiment_vector": 0.0, "total_weight": 0.0} for asset in TARGET_ASSETS}

    with open("tagged_model_matrix.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        parsed = parse_tagged_line(line.strip())
        if not parsed:
            continue
            
        decay = parsed["decay"]
        body = parsed["body"]
        model = parsed["model"]
        
        # Calculate raw score base on model classification tag
        if model == "[MODEL:NUMERICAL_DELTA]":
            raw_score = evaluate_numerical_delta(body)
            vector_key = "hard_data_vector"
        else:
            raw_score = evaluate_lexicon_tone(body)
            vector_key = "soft_sentiment_vector"
            
        # Apply time-decay scaling matrix across all matching assets
        scaled_score = raw_score * decay
        for asset in parsed["assets"]:
            if asset in scoring_matrix:
                scoring_matrix[asset][vector_key] += scaled_score
                scoring_matrix[asset]["total_weight"] += decay

    # Format output signals matrix
    final_regime_matrix = {}
    for asset, vectors in scoring_matrix.items():
        hard = vectors["hard_data_vector"]
        soft = vectors["soft_sentiment_vector"]
        # Divergence model equation: Measures variation between hard conditions and soft expectations
        divergence = hard - soft
        
        final_regime_matrix[asset] = {
            "hard_macro_score": round(hard, 4),
            "soft_sentiment_score": round(soft, 4),
            "structural_divergence_gap": round(divergence, 4),
            "data_density_weight": round(vectors["total_weight"], 4)
        }

    with open("final_sentiment_matrix.json", "w", encoding="utf-8") as f:
        json.dump(final_regime_matrix, f, indent=4)
        
    print("Macro sentiment scoring matrix successfully compiled.")

if __name__ == "__main__":
    generate_sentiment_matrix()
