import csv
import json
from pathlib import Path

# CONFIGURATION
CSV_FILE_PATH = Path("setup/data/historic_openings.csv")
OUTPUT_DIRECTORY = Path("setup/data/bet_placings")

def clean_value(val: str, default: str = "") -> str:
    """Removes leading/trailing whitespaces and normalises dashes or blanks."""
    cleaned = val.strip()
    if cleaned in ("-", "", None):
        return default
    return cleaned

def split_csv_to_json():
    # Ensure output directory exists
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    
    if not CSV_FILE_PATH.exists():
        print(f"Error: {CSV_FILE_PATH} does not exist.")
        return

    count = 0
    with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Map CSV headers directly to OpenBetUpdate Pydantic Schema elements
            bet_id = row["ID"].strip()
            
            json_payload = {
                "ID": bet_id,
                "bookmaker": row["Bookmaker"].strip(),
                "oddsTaken": row["Taken"].strip(),
                "bog": clean_value(row["BOG?"], default="-"),
                "placesPaid": clean_value(row["PlcPaid"], default="-"),
                "placeFraction": clean_value(row["PlcFraction"], default="-"),
                "gbpPerPoint": float(row["PtGBP"].strip())
            }
            
            # Save payload to unique JSON file named by the Bet ID
            output_file = OUTPUT_DIRECTORY / f"{bet_id}.json"
            with open(output_file, mode="w", encoding="utf-8") as out_f:
                json.dump(json_payload, out_f, indent=4, ensure_ascii=False)
            
            count += 1

    print(f"Successfully split {count} rows into individual JSON files inside '{OUTPUT_DIRECTORY}'.")

if __name__ == "__main__":
    split_csv_to_json()
