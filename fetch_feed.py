import csv
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# 1. Deduplicated Global Macro Account Pool (58 total)
TARGET_ACCOUNTS = [
    'zerohedge', 'financialjuice', 'Globalflows', 'GlobalMacroZen', 'iv_technicals', 
    'kirstenbartok', 'pavelprata', 'JohnKicklighter', 'HooverInst', 'clashreport', 
    'YCCMacro', 'TrumpWarRoom', 'ExanteData', 'glcarlstrom', 'pradeeepk', 
    'KobeissiLetter', 'spectatorindex', 'sentdefender', 'michaeljburry', 'staunovo', 
    'aeberman12', 'C_Barraud', 'HFI_Research', 'BarakRavid', 'vvanwilgenburg', 
    'RusOilGasExpert', 'LayoffAI', 'Mr_Derivatives', 'Osint613', 'mb_ghalibaf', 
    'hey_itsmyturn', 'grahamformaine', 'HannoLustig', 'MarkHorowitz', 'DeItaone', 
    'zeibars', 'Kalshi', 'robin_j_brooks', 'iimag', 'PeakoQuant', 
    'Alpha_Ex_LLC', 'themarketear', 'topdowncharts', 'Brad_Setser', 'KoyfinCharts', 
    'Econimica', 'JosephPolitano', 'EPBResearch', 'WarrenPies', 'lisaabramowicz1', 
    'elerianm', 'beth_stanton', 'Skycastle_int', 'VrntPerception', 'marcmakingsense', 
    'Schuldensuehner', 'Callum_Thomas', 'samueltombs', 'cbrates', 'sentimentrader'
]

# 2. Resilient Open-Source RSS Gateway
NITTER_INSTANCE = "https://privacydev.net"

def fetch_user_feed(username):
    url = f"{NITTER_INSTANCE}/{username}/rss"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SystematicMacroBot/1.0'}
    req = urllib.request.Request(url, headers=headers)
    
    tweets = []
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                # Strip internal URL routing to isolate numeric Tweet ID
                tweet_id = link.split('/')[-1].split('#')[0] if '/' in link else pub_date
                
                # Prevent empty content row append crashes
                if title and tweet_id:
                    tweets.append([tweet_id, username, pub_date, title])
    except Exception as e:
        # Graceful degradation ensures one down account won't crash the whole run
        print(f"Skipping @{username}: Connection Timeout or Invalid Route ({e})")
    return tweets

# 3. Batch Process Sequence
print(f"Initiating automated pipeline pull across {len(TARGET_ACCOUNTS)} active macro nodes...")
all_tweets = []
for index, user in enumerate(TARGET_ACCOUNTS, 1):
    print(f"[{index}/{len(TARGET_ACCOUNTS)}] Processing @{user}...")
    all_tweets.extend(fetch_user_feed(user))

# 4. Atomic Write to tracking matrix
with open("tracker.csv", mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Tweet_ID", "Account", "Date_Logged", "Tweet_Text"])
    writer.writerows(all_tweets)

print(f"Pipeline complete. Ingested {len(all_tweets)} potential market signals into tracker.csv.")
