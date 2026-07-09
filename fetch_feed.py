import csv
import logging
import urllib.request
import xml.etree.ElementTree as ET
import time

# Configure local logging to surface on the GitHub actions stdout
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Dynamic instance list to safeguard against IP blocks or temporary rate limits
NITTER_INSTANCES = [
    "https://poast.org",
    "https://privacydev.net",
    "https://privacydev.net",
    "https://nitter.cz"
]

# Example minimal test array (Substitute with your 58 deduplicated handles)
TARGET_HANDLES = ["financialjuice", "GlobalMacroZen", "YCCMacro", "ExanteData", "Econimica"]

def fetch_rss_with_failover(handle):
    # Ensure any misplaced '@' signs are stripped from strings
    clean_handle = handle.lstrip('@')
    
    for instance in NITTER_INSTANCES:
        url = f"{instance}/{clean_handle}/rss"
        logging.debug(f"Attempting vector download: {url}")
        
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SystematicMacroEngine/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=12) as response:
                status = response.getcode()
                logging.debug(f"HTTP Status: {status} from {instance}")
                
                if status != 200:
                    continue
                    
                raw_data = response.read()
                
                # Check for explicit empty string returns
                if not raw_data or len(raw_data.strip()) == 0:
                    logging.warning(f"Blank payload returned from {instance} for @{clean_handle}")
                    continue
                
                # Test XML/RSS validity before proceeding
                root = ET.fromstring(raw_data)
                items = root.findall('.//item')
                
                if len(items) == 0:
                    logging.warning(f"Valid XML format but contains 0 items on instance: {instance}")
                    continue
                
                logging.info(f"Successfully extracted {len(items)} posts from {instance} for @{clean_handle}")
                return items # Break loop early on successful extraction
                
        except ET.ParseError as xml_err:
            logging.error(f"Malformed XML markup received from {instance}: {str(xml_err)}")
        except Exception as e:
            logging.warning(f"Connection breakdown on instance {instance}: {str(e)}")
            
        # Linear rate limiting backoff before trying the next available server proxy
        time.sleep(1.5)
        
    logging.critical(f"Total upstream data ingest failure across all pools for handle: @{clean_handle}")
    return []

# Execute and dump results to file pipeline
with open('tracker.csv', mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['handle', 'title', 'description', 'pubDate'])
    
    for target in TARGET_HANDLES:
        posts = fetch_rss_with_failover(target)
        for post in posts:
            title = post.find('title').text if post.find('title') is not None else ""
            desc = post.find('description').text if post.find('description') is not None else ""
            date = post.find('pubDate').text if post.find('pubDate') is not None else ""
            writer.writerow([target, title, desc, date])
