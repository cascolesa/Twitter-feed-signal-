import csv
import logging
import urllib.request
import xml.etree.ElementTree as ET
import time

# Configure clean logging output for GitHub Actions runner console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Geographically distributed public RSSHub mirror instances
RSSHUB_INSTANCES = [
    "https://rsshub.rssforever.com",
    "https://moeyy.xyz",
    "https://rsshub.app"
]

# Core macroeconomic accounts target tracking vector
TARGET_HANDLES = ["financialjuice", "GlobalMacroZen", "YCCMacro", "ExanteData", "Econimica"]

def fetch_rsshub_with_failover(handle):
    # Sanitize user string context to match endpoint schema paths
    clean_handle = handle.lstrip('@')
    
    for instance in RSSHUB_INSTANCES:
        # Standardized RSSHub Twitter user endpoint route string
        url = f"{instance}/twitter/user/{clean_handle}"
        logging.debug(f"Connecting to RSSHub Matrix Route: {url}")
        
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SystematicEngine/2.0'}
            )
            
            # Explicit timeout limit to prevent GitHub runner hanging loops
            with urllib.request.urlopen(req, timeout=15) as response:
                status = response.getcode()
                logging.debug(f"HTTP Return Status: {status} from node [{instance}]")
                
                if status != 200:
                    continue
                    
                raw_data = response.read()
                
                if not raw_data or len(raw_data.strip()) == 0:
                    logging.warning(f"Node response contains null bytes on {instance} for handle: @{clean_handle}")
                    continue
                
                # Dynamic XML processing checkpoint
                root = ET.fromstring(raw_data)
                items = root.findall('.//item')
                
                if len(items) == 0:
                    logging.warning(f"Valid RSSHub wrapper structural check, but 0 items listed on {instance}")
                    continue
                
                logging.info(f"Successfully processed {len(items)} items from {instance} for target @{clean_handle}")
                return items
                
        except ET.ParseError as xml_fault:
            logging.error(f"Malformed structural layout on node {instance}: {str(xml_fault)}")
        except Exception as conn_error:
            logging.warning(f"Connection pool failure on routing node {instance}: {str(conn_error)}")
            
        # Throttling step to respect server backplanes
        time.sleep(2.0)
        
    logging.critical(f"Upstream pipeline down. All instances exhausted for handle: @{clean_handle}")
    return []

# Execute pipeline compilation and commit arrays to local file system
with open('tracker.csv', mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['handle', 'title', 'description', 'pubDate'])
    
    for target in TARGET_HANDLES:
        posts = fetch_rsshub_with_failover(target)
        for post in posts:
            title = post.find('title').text if post.find('title') is not None else ""
            desc = post.find('description').text if post.find('description') is not None else ""
            date = post.find('pubDate').text if post.find('pubDate') is not None else ""
            writer.writerow([target, title, desc, date])
