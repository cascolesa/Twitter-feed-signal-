import asyncio
import os
import re
import csv
import datetime
import yfinance as yf
from twikit import Client

# CONFIGURATION
LIST_ID = "2074473804835729447"  
CSV_FILE = "tracker.csv"
SCORECARD_FILE = "scorecard.csv"
HOLDING_PERIOD_DAYS = 90  # Strict 1-quarter fundamental evaluation window

AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
CT0 = os.getenv("X_CT0")

client = Client(
    language="en-US",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# ALL-INCLUSIVE MASTER DICTIONARY: Maps global assets to Yahoo Finance symbols
MACRO_MAP = {
    # --- Major Global Indices ---
    "s&p 500": "^GSPC", "s&p": "^GSPC", "spy": "SPY",
    "nasdaq": "^IXIC", "nasdaq 100": "^NDX", "qqq": "QQQ",
    "dow jones": "^DJI", "dow": "^DJI", "dia": "DIA",
    "russell 2000": "^RUT", "iwm": "IWM",
    "vix": "^VIX", "volatility index": "^VIX",
    "ftse": "^FTSE", "dax": "^GDAXI", "nikkei": "^N225",
    
    # --- Fixed Income & Bonds (Yields) ---
    "10y yield": "^TNX", "10-year treasury": "^TNX", "10y treasury": "^TNX", "bonds": "^TNX",
    "2y yield": "^IRX", "2-year treasury": "^IRX", "2y treasury": "^IRX",
    "30y yield": "^TYX", "30-year treasury": "^TYX", "30y treasury": "^TYX",
    
    # --- Top Cryptocurrencies ---
    "bitcoin": "BTC-USD", "btc": "BTC-USD",
    "ethereum": "ETH-USD", "eth": "ETH-USD",
    "solana": "SOL-USD", "sol": "SOL-USD",
    "binance coin": "BNB-USD", "bnb": "BNB-USD",
    "ripple": "XRP-USD", "xrp": "XRP-USD",
    "cardano": "ADA-USD", "ada": "ADA-USD",
    
    # --- Energy ---
    "crude oil": "CL=F", "crude": "CL=F", "wti": "CL=F", "brent": "BZ=F",
    "natural gas": "NG=F", "natgas": "NG=F", "gasoline": "RB=F",
    
    # --- Precious & Industrial Metals ---
    "gold": "GC=F", "silver": "SI=F", "copper": "HG=F", "platinum": "PL=F",
    
    # --- Agriculture ---
    "corn": "ZC=F", "wheat": "ZW=F", "soybeans": "ZS=F", "coffee": "KC=F",
    
    # --- Major Currencies ---
    "dollar index": "DX-Y.NYB", "dxy": "DX-Y.NYB",
    "swiss franc": "CHFUSD=X", "chf": "CHFUSD=X",
    "euro": "EURUSD=X", "eur": "EURUSD=X",
    "pound": "GBPUSD=X", "gbp": "GBPUSD=X",
    "yen": "JPYUSD=X", "jpy": "JPYUSD=X"
}

# STEP A: BROAD STRUCTURAL METRIC VOCABULARY
FUNDAMENTAL_KEYWORDS = [
    # Earnings & Corporate Health
    "eps", "earnings", "yoy", "qoq", "margin", "revenue", "valuation", "pe ratio", 
    "balance sheet", "guidance", "free cash flow", "ebitda", "p/e", "capex", "net income",
    
    # Monetary Policy & Central Banks
    "fed", "rate cut", "hike", "fomc", "hawkish", "dovish", "interest rates", 
    "liquidity", "quantitative easing", "qe", "qt", "ecb", "boj", "central bank",
    
    # Macro Indicators
    "inflation", "cpi", "yield curve", "macro", "recession", "gdp", "pmi", "pce", 
    "stagflation", "deflation", "velocity", "soft landing", "hard landing",
    
    # Labor & Economic Health
    "unemployment", "payrolls", "nfp", "wages", "labor market", "consumer spending",
    "retail sales", "housing starts", "consumer confidence", "debt", "deficit",
    
    # Commodity & Supply Mechanics
    "inventory", "supply chain", "opec", "production capacity", "shale", "deficit", "surplus"
]

def is_fundamentally_valid(text):
    """Verifies the text matches at least one broad macro or corporate structural variable."""
    clean_text = text.lower()
    return any(keyword in clean_text for keyword in FUNDAMENTAL_KEYWORDS)

def parse_asset_ticker(text):
    clean_text = text.lower()
    for keyword, ticker in MACRO_MAP.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', clean_text):
            return ticker
    match = re.search(r'\$([A-Z]{1,5})', text)
    if match:
        return match.group(1)
    words = re.findall(r'\b[A-Z]{3,5}\b', text)
    for word in words:
        if word not in ["AND", "THE", "FOR", "NOW", "FED", "CPI", "USA", "GDP", "THEY", "WITH", "THAT", "THIS"]:
            return word
    return None

def process_and_score_metrics():
    if not os.path.exists(CSV_FILE):
        return
        
    rows = []
    analyst_stats = {}
    now = datetime.datetime.now()
    
    with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
            rows.append(header)
        except StopIteration:
            return
            
        for row in reader:
            if not row: continue
            tweet_id, account, date_str, text, ticker, entry_p, current_p, perf, status = row
            
            entry_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            days_elapsed = (now - entry_date).days
            
            if status == "OPEN":
                try:
                    stock = yf.Ticker(ticker)
                    live_price = stock.history(period="1d")['Close'].iloc[-1]
                    live_price = round(live_price, 2)
                    entry_p_float = float(entry_p)
                    
                    current_perf = round(((live_price - entry_p_float) / entry_p_float) * 100, 2)
                    perf = f"{current_perf}%"
                    current_p = str(live_price)
                    
                    if days_elapsed >= HOLDING_PERIOD_DAYS:
                        status = "MATURED_WIN" if current_perf > 0 else "MATURED_LOSS"
                except Exception:
                    pass
            
            rows.append([tweet_id, account, date_str, text, ticker, entry_p, current_p, perf, status])
            
            if account not in analyst_stats:
                analyst_stats[account] = {"total": 0, "wins": 0, "losses": 0, "open": 0}
                
            analyst_stats[account]["total"] += 1
            if "WIN" in status:
                analyst_stats[account]["wins"] += 1
            elif "LOSS" in status:
                analyst_stats[account]["losses"] += 1
            else:
                analyst_stats[account]["open"] += 1

    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # STEP C EXECUTION: Build and rank the Analyst Scorecard file safely
    header_row = ["Analyst_Handle", "Total_Forecasts", "Matured_Wins", "Matured_Losses", "Active_Open", "Win_Rate_%", "Status_Flag"]
    data_rows = []
    
    for account, stats in analyst_stats.items():
        matured_total = stats["wins"] + stats["losses"]
        win_rate = 0.0
        if matured_total > 0:
            win_rate = round((stats["wins"] / matured_total) * 100, 2)
            
        flag = "ELITE" if win_rate >= 60.0 and matured_total >= 3 else "UNDER_REVIEW"
        if win_rate < 45.0 and matured_total >= 3:
            flag = "POOR_FORECASTER_FLAG"
            
        data_rows.append([
            account, stats["total"], stats["wins"], stats["losses"], stats["open"], f"{win_rate}%", flag
        ])
        
    # Corrected row-indexing syntax map sorting filter
    data_rows.sort(key=lambda x: float(x[5].replace('%', '')), reverse=True)
    
    with open(SCORECARD_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header_row)
        writer.writerows(data_rows)
    print("Analyst Scorecard compilation completed successfully.")

async def main():
    print("Initializing tracker data audits & analytics...")
    process_and_score_metrics()

    if not AUTH_TOKEN or not CT0:
        print("CRITICAL ERROR: Missing token environment secrets.")
        return
        
    client.set_cookies({'auth_token': AUTH_TOKEN, 'ct0': CT0})

    try:
        print(f"Connecting to X API to pull list ID: {LIST_ID}")
        tweets = await client.get_list_tweets(LIST_ID, count=50)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed pulling list feed: {e}")
        return

            existing_ids = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row and len(row) > 0:
                    existing_ids.add(row[0])


        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row: existing_ids.add(row)

    new_trades_count = 0
    print(f"Found {len(tweets)} recent tweets. Filtering for broad structural metric vocabulary...")

    for tweet in tweets:
        if tweet.id in existing_ids:
            continue
            
        if not is_fundamentally_valid(tweet.text):
            print(f"Skipped tweet ID {tweet.id}: Fails quality check (No structural metric vocabulary found).")
            continue
            
        ticker = parse_asset_ticker(tweet.text)
        if ticker:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if hist.empty:
                    continue
                entry_price = hist['Close'].iloc[-1]
                entry_price = round(entry_price, 2)
                account_handle = tweet.user.screen_name
                
                with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        tweet.id,
                        account_handle,
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        tweet.text.replace("\n", " "), 
                        ticker, 
                        entry_price, 
                        entry_price, 
                        "0.0%", 
                        "OPEN"
                    ])
                new_trades_count += 1
                print(f"SUCCESS: Logged high-quality fundamental thesis on {ticker} from @{account_handle}")
            except Exception:
                pass

    print(f"Run finished completely. Appended {new_trades_count} valid structural posts.")

if __name__ == "__main__":
    asyncio.run(main())
