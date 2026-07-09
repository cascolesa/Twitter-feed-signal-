import csv
import logging
import urllib.request
import json
import os
import re
import time

# Configure logging for GitHub Actions runner stdout
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Reads the mapped token passed dynamically via the workflow env block
X_AUTH_TOKEN = os.environ.get("TWITTER_AUTH_TOKEN")

# Core macro account targets vector
TARGET_HANDLES = ["financialjuice", "GlobalMacroZen", "YCCMacro", "ExanteData", "Econimica"]

def fetch_timeline_via_auth(handle):
    if not X_AUTH_TOKEN:
        logging.critical("CRITICAL: TWITTER_AUTH_TOKEN secret mapping missing from execution context.")
        return []
        
    clean_handle = handle.lstrip('@')
    url = f"https://twitter.com{clean_handle}"
    logging.debug(f"Querying secure authenticated timeline for: @{clean_handle}")
    
    try:
        req = urllib.request.Request(url)
        # Mimic desktop chrome footprints to pass client verification protocols smoothly
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        req.add_header('Cookie', f'auth_token={X_AUTH_TOKEN}')
        
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.getcode() != 200:
                logging.warning(f"Server rejected token handshake with status code: {response.getcode()}")
                return []
                
            html_content = response.read().decode('utf-8')
            
            # Extract underlying timeline context state out of the native script layout tags
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content)
            if not match:
                match = re.search(r'<script id="__INITIAL_STATE__" type="application/json">(.*?)</script>', html_content)
                
            if match:
                data = json.loads(match.group(1))
                entries = data.get("props", {}).get("pageProps", {}).get("timeline", {}).get("entries", [])
                logging.info(f"Successfully extracted {len(entries)} raw timeline entries for @{clean_handle}")
                return entries
                
            logging.warning(f"Could not locate matching target state JSON bundle for @{clean_handle}")
            return []
            
    except Exception as e:
        logging.error(f"Authorized validation handshake failed for @{clean_handle}: {str(e)}")
        return []

# Execute processing matrix data compilation loop
with open('tracker.csv', mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['handle', 'title', 'description', 'pubDate'])
    
    for target in TARGET_HANDLES:
        entries = fetch_timeline_via_auth(target)
        for entry in entries:
            tweet = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
            legacy = tweet.get("legacy", {})
            
            text = legacy.get("full_text", "")
            date = legacy.get("created_at", "")
            
            if text:
                writer.writerow([target, "Tweet", text, date])
                
        # Flow rate buffer delay to emulate baseline scrolling
        time.sleep(2.0)
