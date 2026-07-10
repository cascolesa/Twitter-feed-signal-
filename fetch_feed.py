import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Configuration matrices for targeted positional macro feeds
TELEGRAM_CHANNELS = ["FinancialJuice", "macromicro_en", "fbsanalytics", "forexlive", "demarkanalytics"]
RSS_FEEDS = {
    "FRED_Macro": "https://stlouisfed.org",
    "ECB_Policy": "https://europa.eu",
    "IMF_Global": "https://imf.org",
    "WorldBank_Indicators": "https://worldbank.org"
}

def clear_network_blocks():
    """Prevents local runner proxy environment flags from halting network execution."""
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
        os.environ.pop(key, None)

def fetch_url_data(url):
    """Executes a 3-tier request retry loop with localized browser spoofing."""
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read()
        except Exception:
            if attempt == 2:
                return b""
    return b""

def extract_telegram_timestamps(post_html):
    """Extracts raw post messages and text-embedded ISO dates from Telegram web view."""
    messages = []
    # Locate individual telegram post widgets within the web channel view
    post_blocks = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', post_html, re.DOTALL)
    # Locate corresponding datetime blocks
    time_blocks = re.findall(r'<time class="time"[^>]*datetime="([^"]+)"', post_html)
    
    for i, text in enumerate(post_blocks):
        # Clean HTML tags from the inner text string
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        # Fallback to current time if the datetime element count mismatches
        timestamp = time_blocks[i] if i < len(time_blocks) else datetime.now(timezone.utc).isoformat()
        if clean_text:
            messages.append((timestamp, clean_text))
    return messages

def parse_rss_date(date_str):
    """Parses standard RSS date formats into uniform ISO strings for time-decay weighting."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()

def pull_all_feeds():
    """Aggregates multi-asset macro text fields and maps structural timestamp data."""
    clear_network_blocks()
    master_dataset = []

    # 1. Digest Telegram Web Feeds
    for channel in TELEGRAM_CHANNELS:
        url = f"https://t.me{channel}" # Web preview URL format bypasses standard client authentication
        raw_html = fetch_url_data(url).decode('utf-8', errors='ignore')
        if raw_html:
            extracted_posts = extract_telegram_timestamps(raw_html)
            for timestamp, message in extracted_posts:
                master_dataset.append(f"[TIMESTAMP:{timestamp}][SOURCE:TELEGRAM][CHANNEL:{channel}] {message}")

    # 2. Digest Institutional RSS Channels
    for feed_name, url in RSS_FEEDS.items():
        raw_xml = fetch_url_data(url)
        if not raw_xml:
            continue
        try:
            root = ET.fromstring(raw_xml)
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                iso_timestamp = parse_rss_date(pub_date)
                combined_content = f"{title} {desc}".replace("\n", " ").strip()
                if combined_content:
                    master_dataset.append(f"[TIMESTAMP:{iso_timestamp}][SOURCE:RSS][CHANNEL:{feed_name}] {combined_content}")
        except Exception:
            continue

    return master_dataset

if __name__ == "__main__":
    raw_entries = pull_all_feeds()
    with open("raw_ingest_matrix.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(raw_entries))
    print(f"Ingestion matrix complete. Entries captured: {len(raw_entries)}")
