import os
import json
import time
import requests
from pathlib import Path
from confidential import HEADERS

# CONFIGURATION
INPUT_DIRECTORY = Path("bet_placings")
API_ENDPOINT = "http://127.0.0.1:8000/bet/open"

def upload_open_bets():
    if not INPUT_DIRECTORY.exists():
        print(f"Error: Target directory '{INPUT_DIRECTORY}' does not exist.")
        return

    # Gather files and sort them naturally by ID string
    json_files = sorted(INPUT_DIRECTORY.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found inside '{INPUT_DIRECTORY}'.")
        return

    success_count = 0
    failed_count = 0

    print(f"Beginning batch update of {len(json_files)} entries to {API_ENDPOINT}...")
    print("-" * 60)

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=HEADERS)
            
            time.sleep(5)  # Sleep to avoid overwhelming the server

            if response.status_code == 200:
                print(f"✅ Bet {payload['ID']} updated to Open status.")
                success_count += 1
            else:
                print(f"❌ Bet {payload['ID']} returned status code {response.status_code}: {response.text}")
                failed_count += 1
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection failure on Bet {payload['ID']}: {e}")
            failed_count += 1
           
    print("-" * 60)
    print(f"Batch update completed: {success_count} succeeded, {failed_count} failed.")
    
if __name__ == "__main__":
    upload_open_bets()
