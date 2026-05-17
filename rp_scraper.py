from dotenv import load_dotenv
load_dotenv()  # This looks for a .env file and loads it into os.environ

import os
import csv
import json
import subprocess
import re
from pathlib import Path
import asyncio
from datetime import datetime

# CONFIGURATION
BASE_DIR = Path(__file__).parent
RPSCRAPE_DIR = BASE_DIR / "rpscrape"
RPSCRAPE_SCRIPT_DIR = RPSCRAPE_DIR / "scripts"
RPSCRAPE_SCRIPT = RPSCRAPE_SCRIPT_DIR / "rpscrape.py"
COURSES_JSON_FILE = RPSCRAPE_DIR / "courses" / "_courses"

# Target file paths
DATA_DIR = RPSCRAPE_DIR / "data" / "course"
CACHE_DIR = RPSCRAPE_DIR / ".cache" / "progress" / "course"

def clean_horse_name(name: str) -> str:
    """Removes suffix country abbreviations like (GB), (IRE), (FR)."""
    if not name: return ""
    return re.sub(r"\s*\([A-Z]{2,3}\)", "", name, flags=re.IGNORECASE).strip()

def clean_sp_odds(sp_str: str) -> str:
    """Strips out Favourite markers like 'F', 'J', 'C' from prices (e.g., '9/4F' -> '9/4')."""
    if not sp_str: return ""
    return re.sub(r"[A-Za-z]+$", "", sp_str.strip())

def lookup_racing_post_course_id(target_name: str):
    """Dynamically loads the _courses file and performs smart matching."""
    if not COURSES_JSON_FILE.exists():
        print(f"Error: Course layout map missing at {COURSES_JSON_FILE}")
        return None
        
    with open(COURSES_JSON_FILE, "r", encoding="utf-8") as f:
        course_data = json.load(f)
        
    search_name = target_name.strip().lower().replace(" ", "-")
    candidates = {}
    
    for region in ["gb", "ire"]:
        if region in course_data:
            for course_id, name in course_data[region].items():
                name_lower = name.lower()
                if name_lower == search_name:
                    return course_id
                if name_lower.startswith(search_name):
                    candidates[name_lower] = course_id

    if not candidates:
        return None
        
    best_match_name = min(candidates.keys(), key=len)
    return candidates[best_match_name]

def run_rpscrape_sync(date_str: str, course_id: str) -> Path:
    """Executes rpscrape with a locked Current Working Directory (CWD)."""
    date_filename = date_str.replace("-", "_")
    expected_csv_path = DATA_DIR / course_id / "all" / f"{date_filename}.csv"
    
    # Internal progress tracking file location
    expected_progress_path = CACHE_DIR / course_id / "all" / f"{date_filename}.progress"
    
    if expected_csv_path.exists() and expected_csv_path.stat().st_size > 100:
        print(f"File {expected_csv_path.name} already exists with valid contents. Skipping download.")
        return expected_csv_path
    else:
        # Clear the broken data file and its progress tag to force a fresh download
        print(f"Valid data file not found or looks corrupt. Forcing a fresh download for course {course_id}...")
        expected_csv_path.unlink(missing_ok=True)
        expected_progress_path.unlink(missing_ok=True)

    # Formulate arguments exactly as rpscrape expects them
    cmd = [
        "python",
        str(RPSCRAPE_SCRIPT),
        "-c", course_id,
        "-d", date_str.replace("-", "/") # Pass as YYYY/MM/DD
    ]
    
    env = os.environ.copy()
    try:
        print(f"Calling rpscrape via subprocess in CWD: {RPSCRAPE_SCRIPT_DIR}")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True, 
            env=env, 
            cwd=str(RPSCRAPE_SCRIPT_DIR)
        )
        print(result.stdout)
        return expected_csv_path
    except subprocess.CalledProcessError as e:
        print(f"Subprocess execution failed (Code {e.returncode}): {e.stderr}")
        return expected_csv_path

async def fetch_race_results(date_param: str, course_name: str, race_time: str):
    dt = datetime.strptime(date_param, "%d-%m-%Y")
    date_iso = dt.strftime("%Y-%m-%d")  
    
    course_id = lookup_racing_post_course_id(course_name)
    if not course_id:
        return {"status": "error", "message": f"Course variant '{course_name}' could not be matched."}
        
    csv_file_path = await asyncio.to_thread(run_rpscrape_sync, date_iso, course_id)
    
    if not csv_file_path.exists() or csv_file_path.stat().st_size <= 100:
        return {"status": "error", "message": f"Scraper executed but data file was not found or remains empty."}
        
    runners = []
    try:
        with open(csv_file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("off", "").strip() == race_time.strip():
                    runners.append({
                        "position": row.get("pos"),
                        "horse": clean_horse_name(row.get("horse", "")),
                        "sp": clean_sp_odds(row.get("sp", ""))
                    })
    except Exception as e:
        return {"status": "error", "message": f"Failed reading generated file data: {e}"}

    if not runners:
        return {"status": "error", "message": f"No runners found matching race time {race_time}."}
        
    return {
        "status": "success",
        "data": {
            "metadata": {
                "date": date_iso,
                "course": course_name,
                "course_rp_id": course_id,
                "off_time": race_time
            },
            "runners": runners
        }
    }
