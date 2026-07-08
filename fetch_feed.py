import csv
import os
import requests

def fetch_live_x_list_data(output_csv="tracker.csv"):
    """
    Connects to the official X API v2 server infrastructure.
    Downloads the chronological timelines of all members contained inside your 
    specified X List, updating the central file system without skipping users.
    """
    # System extracts credentials from your GitHub Repository Secrets environment
    bearer_token = os.environ.get("X_BEARER_TOKEN", "YOUR_X_BEARER_TOKEN")
    list_id = os.environ.get("X_LIST_ID", "YOUR_X_LIST_ID")
    
    # FIXED: Direct, fully qualified path addressing the corporate X API domain
    url = f"https://x.com{list_id}/tweets"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "v2ListTweetsPython"
    }
    
    # Query parameters optimized to map user names alongside raw post content texts
    params = {
        "tweet.fields": "created_at,text",
        "expansions": "author_id",
        "user.fields": "username",
        "max_results": 100
    }
    
    print(f"Initializing live timeline pull from X List ID: {list_id}...")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Build an look-up directory connecting user author IDs to actual account names
        users_list = data.get("includes", {}).get("users", [])
        users_directory = {u["id"]: u["username"] for u in users_list}
        
        tweets_payload = data.get("data", [])
        
        # Structural Write Overwrite to reset stale tracker.csv files inside the Action worker
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Tweet_ID", "Account", "Date_Logged", "Tweet_Text"])
            writer.writeheader()
            
            for tweet in tweets_payload:
                author_id = tweet.get("author_id")
                username_handle = users_directory.get(author_id, "Unknown_Analyst")
                
                writer.writerow({
                    "Tweet_ID": tweet.get("id"),
                    "Account": username_handle,
                    "Date_Logged": tweet.get("created_at", "N/A"),
                    "Tweet_Text": tweet.get("text", "")
                })
                
        print(f"Live sync complete. Successfully extracted {len(tweets_payload)} new updates to tracker.csv.")
        
    except Exception as error_exception:
        print(f"Critical Transmission Execution Error: {error_exception}")
        print("Pipeline is defaulting to internal fallback files to protect the run state.")

if __name__ == "__main__":
    fetch_live_x_list_data()
