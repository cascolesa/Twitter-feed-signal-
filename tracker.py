import asyncio
import os
import re
import csv
import datetime
import yfinance as yf
from twikit import Client

LIST_ID = "2074473804835729447"  
CSV_FILE = "tracker.csv"
SCORECARD_FILE = "scorecard.csv"
HOLDING_PERIOD_DAYS = 90  

AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
CT0 = os.getenv("X_CT0")

client = Client(
    language="en-US",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36"
)

MACRO_MAP = {
    "s&p 500": "^GSPC", "s&p": "^GSPC", "spy": "SPY",
    "nasdaq": "^IXIC", "nasdaq 100": "^NDX", "qqq": "QQQ",
    "dow jones": "^DJI", "dow": "^DJI", "dia": "DIA",
    "russell 2000": "^RUT", "iwm": "IWM",
    "vix": "^VIX", "volatility index": "^VIX",
    "ftse": "^FTSE", "dax": "^GDAXI", "nikkei": "^N225",
    "10y yield": "^TNX", "10-year treasury": "^TNX", "10y treasury": "^TNX", "bonds": "^TNX",
    "2y yield": "^IRX", "2-year treasury": "^IRX", "2y treasury": "^IRX",
    "30y yield": "^TYX", "30-year treasury": "^TYX", "30y treasury": "^TYX",
    "bitcoin": "BTC-USD", "btc": "BTC-USD",
    "ethereum": "ETH-USD", "eth": "ETH-USD",
    "solana": "SOL-USD", "sol": "SOL-USD",
    "binance coin": "BNB-USD", "bnb": "BNB-USD",
    "ripple": "XRP-USD", "xrp": "XRP-USD",
    "cardano": "ADA-USD", "ada": "ADA-USD",
    "crude oil": "CL=F", "crude": "CL=F", "wti": "CL=F", "brent": "BZ=F",
    "natural gas": "NG=F", "natgas": "NG=F", "gasoline": "RB=F",
    "gold": "GC=F", "silver": "SI=F", "copper": "HG=F", "platinum": "PL=F",
    "corn": "ZC=F", "wheat": "ZW=F", "soybeans": "ZS=F", "coffee": "KC=F",
    "dollar index": "DX-Y.NYB", "dxy": "DX-Y.NYB",
    "swiss franc": "CHFUSD=X", "chf": "CHFUSD=X",
    "euro": "EURUSD=X", "eur": "EURUSD=X",
    "pound": "GBPUSD=X", "gbp": "GBPUSD=X",
    "yen": "JPYUSD=X", "jpy": "JPYUSD=X"
}

FUNDAMENTAL_KEYWORDS = [
    "eps", "earnings", "yoy", "qoq", "margin", "revenue", "valuation", "pe ratio", 
    "balance sheet", "guidance", "free cash flow", "ebitda", "p/e", "capex", "net income",
    "fed", "rate cut", "hike", "fomc", "hawkish", "dovish", "interest rates", 
    "liquidity", "quantitative easing", "qe", "qt", "ecb", "boj", "central bank",
    "inflation", "cpi", "yield curve", "macro", "recession", "gdp", "pmi", "pce", 
    "stagflation", "deflation", "velocity", "soft landing", "hard landing",
    "unemployment", "payrolls", "nfp", "wages", "labor market", "consumer spending",
    "retail sales", "housing starts", "consumer confidence", "debt", "deficit",
    "inventory", "supply chain", "opec", "production capacity", "shale", "surplus"
]

def is_fundamentally_valid(text):
    clean_text = text.lower()
    for keyword in FUNDAMENTAL_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', clean_text):
            return True
    return False

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
        if word not in [
            "AND", "THE", "FOR", "NOW", "FED", "CPI", "USA", "GDP", "THEY", "WITH", 
            "THAT", "THIS", "WATCH", "BREAKING", "NEWS", "ALERT", "LIVE", "VIDEO", 
            "UAE", "RSF", "INFO", "POST", "NATO", "EURO", "DROP", "MOM", "YOY", "QOQ"
        ]:
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
            if not row or len(row) < 9: continue
            tweet_id, account, date_str, text, ticker, entry_p, current_p, perf, status = row[:9]
            
            # Runtime cleanup: Drop historical bad entries dynamically
            if ticker in ["NATO", "DROP", "EURUSD=X"] and account == "clashreport":
                continue
                
            try:
                entry_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                days_elapsed = (now - entry_date).days
            except ValueError:
                continue
            
            if status == "OPEN":
                try:
                    stock = yf.Ticker(ticker)
                    live_price = stock.history(period="1d")['Close'].iloc[-1]
                    live_price = round(live_price, 2)
                    entry_p_float = float(entry_p)
                    
                    if entry_p_float > 0:
                        current_perf = round(((live_price - entry_p_float) / entry_p_float) * 100, 2)
                        perf = f"{current_perf}%"
                    else:
                        current_perf = 0.0
                        perf = "0.0%"
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
        
    if data_rows:
        data_rows.sort(key=lambda x: float(x[5].replace('%', '')), reverse=True)
    
    with open(SCORECARD_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header_row)
        writer.writerows(data_rows)
    print("Analyst Scorecard compilation completed successfully.")

async def main():
    print("Initializing tracker data audits & analytics...")
    
    if not AUTH_TOKEN or not CT0:
        print("CRITICAL ERROR: Missing token environment secrets.")
        return
        
    client.set_cookies({'auth_token': AUTH_TOKEN, 'ct0': CT0})

    try:
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

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    new_rows = []
    for tweet in tweets:
        if tweet.id in existing_ids or str(tweet.id) in existing_ids:
            continue
            
        text = tweet.text
        if not is_fundamentally_valid(text):
            continue
            
        ticker = parse_asset_ticker(text)
        if not ticker or ticker in ["NATO", "EURO", "DROP"]:
            continue
            
        entry_price = "0.0"
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                entry_price = str(round(hist['Close'].iloc[-1], 2))
        except Exception:
            pass

        if entry_price == "0.0" or entry_price == "0":
            continue

        new_rows.append([tweet.id, tweet.user.screen_name, now_str, text, ticker, entry_price, entry_price, "0.0%", "OPEN"])

    if new_rows:
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Tweet_ID", "Account", "Date_Logged", "Tweet_Text", "Ticker", "Entry_Price", "Current_Price", "Performance", "Status"])
            writer.writerows(new_rows)
            
    process_and_score_metrics()

if __name__ == "__main__":
    asyncio.run(main())
