import csv
import json
from pathlib import Path

# CONFIGURATION
CSV_FILE_PATH = Path("setup/data/historic_settlements.csv")
OUTPUT_DIRECTORY = Path("setup/data/bet_settlements")

def clean_int_value(val: str):
    """Safely converts rule 4 values to integers or None if missing."""
    cleaned = val.strip()
    if cleaned in ("", "-", None):
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None

def split_csv_to_json():
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    
    if not CSV_FILE_PATH.exists():
        print(f"Error: {CSV_FILE_PATH} does not exist.")
        return

    count = 0
    with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            bet_id = row["ID"].strip()
            
            # Formulate structural JSON payload according to SettleBet Pydantic model
            json_payload = {
                "ID": bet_id,
                "status": row["Status"].strip(),       # Won, Placed, Lost, Void
                "position": row["Position"].strip(),   # 1, 2, PU, F, NR etc.
                "sp": row["SP"].strip(),               # Starting Price
                "rule4": clean_int_value(row["R4 %"]), # Optional numeric value
                "comment": row.get("Comments", "").strip() # Optional comment string
            }
            
            output_file = OUTPUT_DIRECTORY / f"{bet_id}.json"
            with open(output_file, mode="w", encoding="utf-8") as out_f:
                json.dump(json_payload, out_f, indent=4, ensure_ascii=False)
            
            count += 1

    print(f"Successfully split {count} settlement rows into '{OUTPUT_DIRECTORY}'.")

if __name__ == "__main__":
    split_csv_to_json()
