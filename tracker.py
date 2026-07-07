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

AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
CT0 = os.getenv("X_CT0")

client = Client(
    language="en-US",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# DICTIONARY: Maps common macro keywords to Yahoo Finance symbols
MACRO_MAP = {
    "crude oil": "CL=F",
    "crude": "CL=F",
    "brent": "BZ=F",
    "wti": "CL=F",
    "gold": "GC=F",
    "silver": "SI=F",
    "dollar index": "DX-Y.NYB",
    "dxy": "DX-Y.NYB",
    "us dollar": "DX-Y.NYB",
    "swiss franc": "CHFUSD=X",
    "chf": "CHFUSD=X",
    "euro": "EURUSD=X",
    "eur": "EURUSD=X",
    "pound": "GBPUSD=X",
    "gbp": "GBPUSD=X",
    "yen": "JPYUSD=X",
    "jpy": "JPYUSD=X",
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD"
}

def parse_asset_ticker(text):
    """Scans tweet for standard cash tags ($AAPL), macro keywords, or isolated uppercase words."""
    clean_text = text.lower()
    
    # 1. Check for macro keywords first (e.g., "crude oil", "swiss franc")
    for keyword, ticker in MACRO_MAP.items():
        if keyword in clean_text:
            return ticker
            
    # 2. Check for standard cash tags (e.g., $AAPL, $TSLA)
    match = re.search(r'\$([A-Z]{1,5})', text)
    if match:
        return match.group(1)
        
    # 3. Check for isolated uppercase financial tags (e.g., standard symbols like NVDA, BTC)
    words = re.findall(r'\b[A-Z]{3,5}\b', text)
    for word in words:
        if word not in ["AND", "THE", "FOR", "NOW", "FED", "CPI", "USA", "GDP", "THEY", "WITH"]:
            return word
            
    return None

def update_tracked_trades():
    if not os.path.exists(CSV_FILE):
        return
    rows = []
    with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
            rows.append(header)
        except StopIteration:
            return
        
        for row in reader:
            if not row: continue
            tweet_id, account, date, text, ticker, entry_p, _, _, status = row
            if status == "OPEN":
                try:
                    stock = yf.Ticker(ticker)
                    current_p = stock.history(period="1d")['Close'].iloc[-1]
                    current_p = round(current_p, 2)
                    entry_p = float(entry_p)
                    perf = round(((current_p - entry_p) / entry_p) * 100, 2)
                    rows.append([tweet_id, account, date, text, ticker, entry_p, current_p, f"{perf}%", "OPEN"])
                except Exception:
                    rows.append(row)
            else:
                rows.append(row)

    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

async def main():
    print("Initializing tracker database updates...")
    update_tracked_trades()

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
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row: existing_ids.add(row[0])

    new_trades_count = 0
    print(f"Found {len(tweets)} recent tweets on the list feed. Scanning for assets...")

    for tweet in tweets:
        if tweet.id in existing_ids:
            continue
            
        ticker = parse_asset_ticker(tweet.text)
        if ticker:
            try:
                stock = yf.Ticker(ticker)
                # Handle edge cases where historical data structure might be empty over weekends
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
                print(f"SUCCESS: Logged asset target {ticker} from analyst @{account_handle}")
            except Exception as e:
                print(f"Skipped asset {ticker} due to financial API error: {e}")
        else:
            print(f"Skipped tweet ID {tweet.id}: Text does not match any tracked financial keyword or ticker.")

    print(f"Run finished completely. Successfully appended {new_trades_count} new entries to tracker.csv.")

if __name__ == "__main__":
    asyncio.run(main())
