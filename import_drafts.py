import os
import json
import requests
from confidential import HEADERS

# Configuration
API_URL = "http://127.0.0.1:8000/bet/draft"
DRAFTS_DIR = "draft_bets"

# HEADERS is defined like this in confidential.py:
# HEADERS = {"x-token": "secret_token_1"}

def import_drafts():
    # Get all json files in the directory
    files = [f for f in os.listdir(DRAFTS_DIR) if f.endswith('.json')]
    
    if not files:
        print("No JSON files found.")
        return

    print(f"Found {len(files)} files. Starting import...")

    for filename in sorted(files):
        file_path = os.path.join(DRAFTS_DIR, filename)
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Send to your FastAPI server
        response = requests.post(API_URL, json=data, headers=HEADERS)
        
        if response.status_code == 200:
            print(f"✅ Imported: {filename} (ID: {data.get('ID')})")
        else:
            print(f"❌ Failed: {filename} - {response.text}")

if __name__ == "__main__":
    import_drafts()
