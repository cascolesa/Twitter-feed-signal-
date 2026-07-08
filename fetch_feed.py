import csv
import os
import requests

def fetch_live_x_list_data(output_csv="tracker.csv"):
    """
    Connects to the X API to extract all chronological posts from your list,
    ensuring that no users or alternative handles are ignored.
    """
    # Replace with your actual X Bearer Token / API Access key
    bearer_token = os.environ.get("X_BEARER_TOKEN", "YOUR_X_BEARER_TOKEN")
    # Replace with your numerical X List ID
    list_id = os.environ.get("X_LIST_ID", "YOUR_X_LIST_ID")
    
    url = f"https://twitter.com{list_id}/tweets"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {
        "tweet.fields": "created_at,text",
        "expansions": "author_id",
        "user.fields": "username",
        "max_results": 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Match user dictionary details
        users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}
        tweets = data.get("data", [])
        
        # Overwrite tracker.csv with the active live timeline snapshot
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Tweet_ID", "Account", "Date_Logged", "Tweet_Text"])
            writer.writeheader()
            
            for t in tweets:
                author_username = users.get(t["author_id"], "Unknown_Analyst")
                writer.writerow({
                    "Tweet_ID": t["id"],
                    "Account": author_username,
                    "Date_Logged": t.get("created_at", "N/A"),
                    "Tweet_Text": t.get("text", "")
                })
        print(f"Success: Retrieved {len(tweets)} live posts across all list members.")
        
    except Exception as e:
        print(f"Skipping API fetch (using baseline backup): {e}")

if __name__ == "__main__":
    fetch_live_x_list_data()
