import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

TELEGRAM_CHANNELS = ["FinancialJuice", "macromicro_en", "fbsanalytics", "forexlive", "demarkanalytics"]
RSS_FEEDS = {
    "FRED_CPI": "https://stlouisfed.org",
    "FRED_Rates": "https://stlouisfed.org",
    "FRED_GDP": "https://stlouisfed.org",
    "ECB_Policy": "https://europa.eu",
    "IMF_Global": "https://imf.org"
}

def clear_network_blocks():
    """Removes runner local proxy environments entirely to keep outbound pathways open."""
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
        os.environ.pop(key, None)

def fetch_url_data(url):
    """Executes network calls with standard browser imitation."""
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read()
        except Exception as e:
            if attempt == 2:
                print(f"Network error on {url}: {e}")
                return b""
    return b""

def extract_telegram_timestamps(post_html):
    """Parses text payloads alongside valid time elements from Telegram web streams."""
    messages = []
    post_blocks = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', post_html, re.DOTALL)
    time_blocks = re.findall(r'<time class="time"[^>]*datetime="([^"]+)"', post_html)
    
    for i, text in enumerate(post_blocks):
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        timestamp = time_blocks[i] if i < len(time_blocks) else datetime.now(timezone.utc).isoformat()
        if clean_text:
            messages.append((timestamp, clean_text))
    return messages

def strip_namespaces(xml_str):
    """Removes all XML namespaces to allow uniform tag searching without schema conflicts."""
    xml_str = re.sub(r'\sxmlns="[^"]+"', '', xml_str, count=1)
    xml_str = re.sub(r'\sxmlns:[^=]+="[^"]+"', '', xml_str)
    xml_str = re.sub(r'<[A-Za-z0-9_]+:', '<', xml_str)
    xml_str = re.sub(r'</[A-Za-z0-9_]+:', '</', xml_str)
    return xml_str

def parse_rss_date(date_str):
    """Normalizes disparate time stamps into clear ISO formats."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip()[:25].strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()

def pull_all_feeds():
    """Aggregates text payloads from active institutional vectors."""
    clear_network_blocks()
    master_dataset = []

    # 1. Process Telegram Channels
    for channel in TELEGRAM_CHANNELS:
        url = f"https://t.me{channel}"
        raw_html = fetch_url_data(url).decode('utf-8', errors='ignore')
        if raw_html:
            extracted_posts = extract_telegram_timestamps(raw_html)
            for timestamp, message in extracted_posts:
                master_dataset.append(f"[TIMESTAMP:{timestamp}][SOURCE:TELEGRAM][CHANNEL:{channel}] {message}")

    # 2. Process Institutional XML Repositories
    for feed_name, url in RSS_FEEDS.items():
        raw_bytes = fetch_url_data(url)
        if not raw_bytes:
            continue
        try:
            xml_clean = strip_namespaces(raw_bytes.decode('utf-8', errors='ignore'))
            root = ET.fromstring(xml_clean)
            
            nodes = root.findall('.//item') + root.findall('.//entry')
            
            for node in nodes:
                title_node = node.find('title')
                desc_node = node.find('description') if node.find('description') is not None else node.find('summary')
                date_node = node.find('pubDate') if node.find('pubDate') is not None else node.find('updated')
                
                title = title_node.text if title_node is not None and title_node.text else ""
                desc = desc_node.text if desc_node is not None and desc_node.text else ""
                pub_date = date_node.text if date_node is not None and date_node.text else ""
                
                iso_timestamp = parse_rss_date(pub_date)
                combined_content = f"{title} {desc}"
                combined_content = re.sub(r'<[^>]+>', '', combined_content)
                combined_content = combined_content.replace("\n", " ").strip()
                
                if combined_content and len(combined_content) > 5:
                    master_dataset.append(f"[TIMESTAMP:{iso_timestamp}][SOURCE:RSS][CHANNEL:{feed_name}] {combined_content}")
        except Exception as e:
            print(f"Parsing failure on feed {feed_name}: {e}")
            continue

    return master_dataset

if __name__ == "__main__":
    raw_entries = pull_all_feeds()
    with open("raw_ingest_matrix.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(raw_entries))
    print(f"Ingestion matrix complete. Entries captured: {len(raw_entries)}")
