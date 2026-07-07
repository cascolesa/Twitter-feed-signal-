import csv
import os
import html
import sys

if not os.path.exists("scorecard.csv"):
    print("No scorecard data computed yet.")
    sys.exit(0)

with open("scorecard.csv", mode='r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader, None)
    try:
        top_row = next(reader)
        top_analyst = top_row[0]
    except StopIteration:
        print("Scorecard is empty.")
        sys.exit(0)

print("==================================================")
print(f"🔥 CURRENT LEADERBOARD WIN-RATE CHAMPION: @{top_analyst}")
print("==================================================")

if not os.path.exists("tracker.csv"):
    print("No historical trade logs found in database.")
    print("==================================================")
    sys.exit(0)

print("📋 LATEST VALID FINANCIAL RESEARCH FROM THIS ACCOUNT:")

target = top_analyst.lower()
with open("tracker.csv", mode='r', encoding='utf-8') as f:
    reader = csv.reader(f)
    try:
        header = next(reader)
    except StopIteration:
        sys.exit(0)
    
    # Direct case-insensitive normalization matching for flexible column headers
    header_lower = [h.lower() for h in header]
    idx_acct = header_lower.index('account') if 'account' in header_lower else 1
    idx_date = header_lower.index('date_logged') if 'date_logged' in header_lower else (header_lower.index('date') if 'date' in header_lower else 2)
    idx_text = header_lower.index('tweet_text') if 'tweet_text' in header_lower else (header_lower.index('text') if 'text' in header_lower else 3)
    idx_tick = header_lower.index('ticker') if 'ticker' in header_lower else 4
    idx_entr = header_lower.index('entry_price') if 'entry_price' in header_lower else 5
    
    matching_rows = []
    for r in reader:
        if len(r) > max(idx_acct, idx_tick) and r[idx_acct].lower() == target:
            matching_rows.append(r)
            
    if matching_rows:
        latest = matching_rows[-1]
        clean_text = html.unescape(latest[idx_text].replace('\n', ' '))
        print(f"• Date: {latest[idx_date]}")
        print(f"• Asset: {latest[idx_tick]}")
        print(f"• Entry: {latest[idx_entr]}")
        print(f"• Summary Text: {clean_text}")
    else:
        print("No recent signals found for this account.")

print("==================================================")
