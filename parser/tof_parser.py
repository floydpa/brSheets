# Parser code for 'Turn Of Foot - Mainline' channel

import re
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class DraftBet:
    ID: str
    tipSent: str
    msgTipSummary: str  # Original, as provided by the tipster
    tipSummary: str     # Parsed tip summary in consistent format
    raceDate: str
    racecourse: str
    raceTime: str
    horse: str
    tipster: str
    stakePts: float
    betType: str
    advisedOdds: str
    advisedPlaces: str

class TurnOfFootParser:
    def __init__(self, input_dir='parser_input', output_dir='parser_output'):
        self.input_path = Path(input_dir)
        self.output_path = Path(output_dir)
        self.output_path.mkdir(exist_ok=True)

    def run(self):
        txt_files = sorted(self.input_path.glob('*.txt'))
        for txt_file in txt_files:
            print(f"Processing: {txt_file.name}")
            json_file = txt_file.with_suffix('.json')
            if not json_file.exists():
                print(f"  [!] Missing {json_file.name}, skipping.")
                continue

            with open(json_file, 'r', encoding='utf-8') as f:
                msg_data = json.load(f)
            
            content = txt_file.read_text(encoding='utf-8')
            bets_with_filenames = self.parse_message(content, msg_data)
            
            for bet, filename in bets_with_filenames:
                output_file = self.output_path / f"{filename}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(bet), f, indent=2, ensure_ascii=False)
            
            print("-" * 50)
            
    def parse_message(self, text, msg_metadata):
        lines = [l.strip() for l in text.replace("\u00A0", " ").splitlines() if l.strip()]
        msg_id = msg_metadata.get('id')
        sent_dt = datetime.fromisoformat(msg_metadata.get('date'))
        
        results = []
        current_course = ""
        global_bet_count = 1

        for line in lines:            
            if re.match(r"^[A-Za-z0-9][A-Za-z0-9\s]*(?:\s*\(.*?\))?$", line):
                clean_course = re.sub(r"\s*\(.*?\)", "", line).strip()
                clean_course = re.sub(r"\s+day\s+\d+", "", clean_course, flags=re.IGNORECASE).strip()
                clean_course = "Cheltenham" if clean_course in ["Day 1", "Day 2", "Day 3", "Day 4"] else clean_course
                current_course = clean_course
                continue

            parsed_batch = self.parse_line(line, current_course, sent_dt, msg_id, global_bet_count)
            for bet_obj, filename in parsed_batch:
                results.append((bet_obj, filename))
                print(f"  {bet_obj.msgTipSummary}")
                print(f"        {bet_obj.tipSummary}")
                global_bet_count += 1
        
        return results

    def expand_shorthand_odds(self, odds_str):
        """Helper to convert standalone shorthand numbers like '33s' or '5s' to '33/1' or '5/1'."""
        # Matches numbers followed by 's' bounded by word boundaries or punctuation
        return re.sub(r'\b(\d+)s\b', r'\1/1', odds_str)

    def parse_line(self, line, course, sent_dt, msg_id, start_count):
        pattern = r"^(?P<time>\d{1,2}[.:]\d{2})\s*-\s*(?P<horses>.+?)\s+(?P<stake>\d+(\.\d+)?)pt\s+(?P<type>win|e/w|ew)\s+(?P<odds>.+)$"
        match = re.search(pattern, line, re.IGNORECASE)
        if not match: return []
        
        raw_time = match.group("time").replace('.', ':')
        horses = [h.strip() for h in match.group("horses").split(",")]
        raw_odds_blob = match.group("odds")
        
        # 1. Expand shorthand 's' markers natively first
        expanded_odds_blob = self.expand_shorthand_odds(raw_odds_blob)

        # 2. Human chatter cleaning array
        chatter_phrases = [
            "Edited", "NRNB",
            "more generally", "generally", "elsewhere", "around", "is ok", "is okay", "otherwise",
            "apiece",
            "hopefully it’ll be more available closer to race time",
            "hopefully it'll be more available closer to race time",
            r"in \d+-\d+ places", r"in \d+ places", "in a few places", "in a few spots",
            "in a place or two", "with a couple of firms", "with a few firms", 
            "at several firms", "at a few firms", "in a place", "in a couple of places",
            "in a couple of spots", "at least"
        ]

        # 3. Clean the odds blob strictly for extracting the true EW places
        clean_for_places = expanded_odds_blob
        for phrase in chatter_phrases:
            clean_for_places = re.sub(rf"\b{phrase}\b", "", clean_for_places, flags=re.IGNORECASE)
            # Fallback for phrases that might contain special characters or boundary issues
            if phrase not in [r"in \d+-\d+ places", r"in \d+ places"]:
                clean_for_places = re.sub(rf"\s*{re.escape(phrase)}\s*", " ", clean_for_places, flags=re.IGNORECASE)

        global_place_match = re.search(r"(?:with\s+)?(?:at\s+least\s+)?(\d+)\s*(?:e[/_]?w\s+)?places?", clean_for_places, re.IGNORECASE)
        places = global_place_match.group(1) if global_place_match else ""

        # 4. Clean odds blob for layout structure evaluation
        clean_odds_blob = re.sub(r"\s+with\s+(?:at\s+least\s+)?\d+\s*(?:e[/_]?w\s+)?places?(?:\s+around)?|\s+(?:at\s+least\s+)?\d+\s*(?:e[/_]?w\s+)?places?", "", raw_odds_blob, flags=re.IGNORECASE).strip()
        for phrase in chatter_phrases:
            clean_odds_blob = re.sub(rf"\s*{phrase}\s*", " ", clean_odds_blob, flags=re.IGNORECASE)
        clean_odds_blob = self.expand_shorthand_odds(clean_odds_blob).strip(", .")

        # 5. ROBUST MULTI-HORSE SPLIT DETECTION
        # Split by comma and find out how many segments actually contain numbers (prices)
        raw_segments = [s.strip() for s in expanded_odds_blob.split(",")]
        price_segments = [s for s in raw_segments if re.search(r"\d+", s)]
        
        # If the number of extracted price tokens matches the horse list count, force multi-horse split mapping
        is_multi_horse_split = len(horses) > 1 and len(price_segments) == len(horses)

        if is_multi_horse_split:
            odds_segments = price_segments
        else:
            odds_segments = [expanded_odds_blob]

        # Time/Date calculation logic
        race_h, race_m = map(int, raw_time.split(':'))
        display_time_h = race_h + 12 if race_h < 11 else race_h
        race_dt = sent_dt
        if display_time_h < sent_dt.hour or (display_time_h == sent_dt.hour and race_m < sent_dt.minute):
            race_dt += timedelta(days=1)

        bet_type = "E/W" if "ew" in match.group("type").lower() or "e/w" in match.group("type").lower() else "Win"
        stake_val = float(match.group("stake"))
        stake_str = f"{int(stake_val) if stake_val.is_integer() else stake_val}pt"

        batch = []
        for i, horse in enumerate(horses):
            if is_multi_horse_split:
                current_segment = odds_segments[i]
                
                segment_place_match = re.search(r"(?:with\s+)?(?:at\s+least\s+)?(\d+)\s*(?:e[/_]?w\s+)?places?", current_segment, re.IGNORECASE)
                if segment_place_match:
                    places = segment_place_match.group(1)
                else:
                    places = global_place_match.group(1) if global_place_match else ""
                
                odds_match = re.search(r"(\d+/\d+|\d+\.\d+|\d+)", current_segment)
                advised_odds = odds_match.group(1) if odds_match else current_segment
                
                summary_odds = re.sub(r"\s+with\s+(?:at\s+least\s+)?\d+\s*(?:e[/_]?w\s+)?places?(?:\s+around)?|\s+(?:at\s+least\s+)?\d+\s*(?:e[/_]?w\s+)?places?", "", current_segment, flags=re.IGNORECASE).strip()
                for phrase in chatter_phrases:
                    summary_odds = re.sub(rf"\s*{phrase}\s*", " ", summary_odds, flags=re.IGNORECASE)
                summary_odds = summary_odds.strip(", .")
            else:
                # --- Single Horse Fallback Logic ---
                general_match = re.search(r"(\d+/\d+|\d+\.\d+|\d+)\s*(?:more\s+)?(?:generally|elsewhere|around|is\s+ok|is\s+okay|(?:is\s+)?ok\s+otherwise|in\s+\d+-\d+\s+places|in\s+\d+\s+places|in\s+a\s+few\s+places|in\s+a\s+few\s+spots)", expanded_odds_blob, re.IGNORECASE)
                
                if general_match:
                    advised_odds = general_match.group(1)
                    summary_odds = advised_odds
                else:
                    first_odds_match = re.search(r"(\d+/\d+|\d+\.\d+|\d+)", expanded_odds_blob)
                    advised_odds = first_odds_match.group(1) if first_odds_match else expanded_odds_blob
                    
                    summary_odds = re.sub(r"\s+with\s+(?:at\s+least\s+)?\d+\s*(?:e[/_]?w\s+)?places?(?:\s+around)?|\s+(?:at\s+least\s+)?\d+\s*(?:e[/_]?w\s+)?places?", "", expanded_odds_blob, flags=re.IGNORECASE).strip()
                    for phrase in chatter_phrases:
                        summary_odds = re.sub(rf"\s*{phrase}\s*", " ", summary_odds, flags=re.IGNORECASE)
                    summary_odds = summary_odds.strip(", .")

            # Construct final clean verification message layout
            summary = f"{course} {display_time_h:02}:{race_m:02} - {horse} {stake_str} {bet_type.lower()} @ {summary_odds}"
            if places: summary += f" with {places} places"

            current_count = start_count + i
            bet = DraftBet(
                ID = f"{msg_id}_{current_count}",
                tipSent = sent_dt.strftime('%Y-%m-%d %H:%M'),
                msgTipSummary = line,
                tipSummary = summary,
                raceDate = race_dt.strftime('%d/%m/%Y'),
                racecourse = course,
                raceTime = f"{display_time_h:02}:{race_m:02}",
                horse = horse,
                tipster = "TOF",
                stakePts = stake_val,
                betType = bet_type,
                advisedOdds = advised_odds, 
                advisedPlaces = places
            )
            filename = f"{sent_dt.strftime('%Y%m%d_%H%M')}_{msg_id}_{current_count}"
            batch.append((bet, filename))
        return batch

if __name__ == "__main__":
    parser = TurnOfFootParser()
    parser.run()
