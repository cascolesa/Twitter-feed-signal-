import os
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def aggregate_scores(file_path="scorecard.csv"):
    """Groups historical sentiment values by asset category to find the net tone."""
    summary = {"forex": [], "commodities": [], "crypto": [], "stocks_and_indices": []}
    if not os.path.exists(file_path): return summary
    with open(file_path, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = row.get("category")
            if cat in summary: summary[cat].append(float(row.get("score", 0)))
    return summary

def construct_and_send_email():
    """Generates the macro text layout and delivers it via Yahoo SMTP."""
    data = aggregate_scores()
    body = "=== AUTOMATED GLOBAL MACRO REPORT ===\n\n"
    
    for asset, scores in data.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        bias = "BULLISH BIAS" if avg > 0.15 else ("BEARISH BIAS" if avg < -0.15 else "NEUTRAL RANGE")
        body += f"[{asset.upper()}]\n - Sentiment Index: {avg:.2f}\n - Forward Outlook: {bias}\n - History Samples: {len(scores)}\n\n"

    # Securely retrieve Yahoo system environment login secrets from GitHub
    sender = os.environ.get("SENDER_EMAIL", "your_account@yahoo.com")
    password = os.environ.get("SENDER_PASSWORD", "yahoo_app_password")
    
    msg = MIMEMultipart()
    msg['From'], msg['To'] = sender, "cascolesa@yahoo.com"
    msg['Subject'] = "Global Macro Narrative Update Report"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to specialized Yahoo outbound mail servers over TLS
        server = smtplib.SMTP("smtp.mail.yahoo.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, msg['To'], msg.as_string())
        server.quit()
        print("Macro brief successfully mailed out via Yahoo Server.")
    except Exception as e:
        print(f"Mail failed to route: {e}\n\nFallback Report View:\n{body}")

if __name__ == "__main__":
    construct_and_send_email()
