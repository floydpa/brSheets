from dotenv import load_dotenv
load_dotenv()  # This looks for a .env file and loads it into os.environ

import os
import json
import time
import requests
from pathlib import Path

# CONFIGURATION
INPUT_DIRECTORY = Path("setup/tmp/bet_settlements")
API_ENDPOINT = "http://127.0.0.1:8000/bet/settle"

HEADERS_JSON = os.environ.get("HEADERS_CONFIG", "{}")
HEADERS = json.loads(HEADERS_JSON)

def upload_settled_bets():
    if not INPUT_DIRECTORY.exists():
        print(f"Error: Target directory '{INPUT_DIRECTORY}' does not exist.")
        return

    json_files = sorted(INPUT_DIRECTORY.glob("*.json"))
    
    if not json_files:
        print(f"No JSON settlement files discovered inside '{INPUT_DIRECTORY}'.")
        return

    success_count = 0
    failed_count = 0

    print(f"Initiating batch transaction processing for {len(json_files)} items...")
    print("=" * 60)

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        try:
            response = requests.post(API_ENDPOINT, json=payload, headers=HEADERS)

            time.sleep(5)  # Sleep to avoid overwhelming the server
            
            if response.status_code == 200:
                print(f"✅ Imported: Bet {payload['ID']} completed successfully.")
                success_count += 1
            else:
                print(f"❌ Failed: Bet {payload['ID']} failed (Code {response.status_code}): {response.text}")
                failed_count += 1
                
        except requests.exceptions.RequestException as e:
            print(f"[CONNECTION ERROR] Failed to push Bet {payload['ID']}: {e}")
            failed_count += 1

    print("=" * 60)
    print(f"Execution complete: {success_count} settled, {failed_count} errors encountered.")

if __name__ == "__main__":
    upload_settled_bets()
