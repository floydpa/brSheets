import os
import json
import gspread
from gspread_formatting import get_user_entered_format, format_cell_range
from gspread_formatting import CellFormat, TextFormat, Color
import threading

# Create a global lock
sheet_lock = threading.Lock()

# Colour to use as background for calculated columns that could be hidden.
CALC_BLUE = Color(207/255, 226/255, 243/255) # #cfe2f3

# Colours for highlighting
GREEN = Color(0, 1, 0)       # #00ff00
RED = Color(234/255, 67/255, 53/255) # #ea4335

# Dark Blue 1 (#1155cc) normalized to 0-1 values for Google API
DARK_BLUE = Color(17/255, 85/255, 204/255)
# Style configuration for overridden formulas: Dark blue text and italicized
AMENDED_FORMAT = CellFormat(
    textFormat=TextFormat(
        foregroundColor=DARK_BLUE,
        italic=True
    )
)

# Auth setup for Google Sheets API using gspread.
# Fetch the JSON string from environment variables
creds_json = os.environ.get("GOOGLE_CREDS_JSON")

if creds_json:
    # If running on Railway/Server, use the environment variable
    creds_dict = json.loads(creds_json)
    gc = gspread.service_account_from_dict(creds_dict)
else:
    # Fallback to local file for development
    gc = gspread.service_account(filename='service_account.json')

def get_user_sheet(sheet_id):
    return gc.open_by_key(sheet_id)

def get_bookmaker_styles(sh):
    config = sh.worksheet("Config")
    # Returns a dict of bookie_name: format_object
    styles = {}
    values = config.get_values("B2:B7") # Adjust range as needed
    for i, row in enumerate(values, start=2):
        name = row[0]
        fmt = get_user_entered_format(config, f"B{i}")
        styles[name] = fmt
    return styles

def get_odds_decimal(odds_str: str):
    if not odds_str or "/" not in odds_str:
        return None
    try:
        num, den = odds_str.split('/')
        return (int(num) / int(den)) + 1
    except (ValueError, ZeroDivisionError):
        return None

def insert_draft_row(sh, bet: dict):
    # This 'with' block ensures only ONE task runs this code at a time
    with sheet_lock:
        ws = sh.worksheet("Transactions")

        # Calculate next row index
        # Note: get_all_values() can be slow on large sheets, 
        # but for <1000 rows it's perfectly fine.
        # idx is always calculated correctly because other threads are waiting
        idx = len(ws.get_all_values()) + 1 
        
        # Prepare the row based on your SheetSpec
        # Columns A-T (Data) + U-AI (Formulas) + AJ (Comment)
        row_data = [
            bet['ID'],              # A: ID
            bet['raceDate'],        # B: Date
            bet['racecourse'],      # C: Racecourse
            bet['raceTime'],        # D: Time
            bet['horse'],           # E: Horse
            bet['tipster'],         # F: Tipster
            bet['stakePts'],        # G: Stake
            bet['betType'],         # H: Bet Type
            bet['advisedOdds'],     # I: AdvOdds
            bet['advisedPlaces'],   # J: AdvPlc
            "-",                    # K: Bookmaker (Default)
            "",                     # L: Taken (Default)
            "-",                    # M: BOG? (Default)
            "",                     # N: PlcPaid (Default)
            "-",                    # O: PlcFraction (Default)
            10.0,                   # P: Pt (£) (Default as requested)
            "Draft",                # Q: Status
            "",                     # R: Position
            "",                     # S: SP
            "",                     # T: R4 %
            f"=YEAR(B{idx})",                                       # U: Year
            f"=MONTH(B{idx})",                                      # V: Month
            f'=IF($L{idx}="","",INT(LEFT($L{idx},FIND("/",$L{idx})-1))/INT(RIGHT($L{idx},LEN($L{idx})-FIND("/",$L{idx})))+1)', # W: DO
            f'=IF(OR($M{idx}<>"Yes",$S{idx}="-",$S{idx}=""),"",1+INT(LEFT($S{idx},FIND("/",$S{idx})-1))/INT(RIGHT($S{idx},LEN($S{idx})-FIND("/",$S{idx}))))', # X: DO (BOG)
            f'=IF($M{idx}<>"Yes",$W{idx},$X{idx})',                 # Y: DO (W)
            f'=IF(OR($O{idx}="",$O{idx}="-"),"",INT(LEFT($O{idx},FIND("/",$O{idx})-1))/INT(RIGHT($O{idx},LEN($O{idx})-FIND("/",$O{idx}))))', # Z: PlcFr
            f'=IF($H{idx}<>"E/W",0,1+(($Y{idx}-1)*$Z{idx}))',       # AA: DO (P)
            f'=IF(OR($Q{idx}="Open",$Q{idx}="Draft"),"",$G{idx}+IF($H{idx}="E/W",$G{idx},0))', # AB: TotalStake (Pts)
            f'=$AB{idx}*$P{idx}',                                   # AC: TotalStake (£)
            f'=IF(OR($Q{idx}="Open",$Q{idx}="Draft"),"",IF($Q{idx}<>"Won",0,$G{idx}*(1+($Y{idx}-1)*IF($T{idx}="",1,1-($T{idx}/100)))))', # AD: Ret (WL)
            f'=IF(OR($Q{idx}="Open",$Q{idx}="Draft"),"",IF(OR($AA{idx}<=0,$Q{idx}="Lost"),0,$G{idx}*(1+($AA{idx}-1)*IF($T{idx}="",1,1-($T{idx}/100)))))', # AE: Ret (PL)
            f'=$AD{idx}+$AE{idx}',                                  # AF: Returns (Pts)
            f'=$AF{idx}-$AB{idx}',                                  # AG: Profit (Pts)
            f'=$AF{idx}*$P{idx}',                                   # AH: Returns (£)
            f'=$AG{idx}*$P{idx}',                                   # AI: Profit (£)
            ""                                                      # AJ: Comment
        ]
    
        # USER_ENTERED is vital so formulas are parsed correctly
        ws.append_row(row_data, value_input_option='USER_ENTERED')
    
        # Apply Blue Background to hidden columns - ID A (1) and calculated U:AE (21 to 31)
        fmt = CellFormat(backgroundColor=CALC_BLUE)
        format_cell_range(ws, f"A{idx}", fmt)
        format_cell_range(ws, f"U{idx}:AE{idx}", fmt)

def update_to_open(sh, update: dict):
    ws_trans = sh.worksheet("Transactions")
    ws_config = sh.worksheet("Config")
    
    # 1. Find the Row Index
    # We fetch column A to find the ID
    ids = ws_trans.col_values(1)
    try:
        # +1 because list index is 0-based and Sheets is 1-based
        row_idx = ids.index(update['ID']) + 1
    except ValueError:
        return False, "ID not found"

    # 2. Prepare the updates for columns K through Q
    # K: Bookmaker, L: Taken, M: BOG?, N: PlcPaid, O: PlcFraction, P: Pt (£), Q: Status
    update_values = [
        update['bookmaker'],
        update['oddsTaken'],
        update['bog'],
        update['placesPaid'],
        update['placeFraction'],
        update['gbpPerPoint'],
        "Open" # Change status from Draft to Open
    ]
    
    # Update the range K{row}:Q{row}
    ws_trans.update(range_name=f"K{row_idx}:Q{row_idx}", 
                    values=[update_values], 
                    value_input_option='USER_ENTERED')

    # 3. Value Analysis for Column L (Taken) vs Column I (Advised)
    advised_str = ws_trans.acell(f"I{row_idx}").value
    adv_dec = get_odds_decimal(advised_str)
    taken_dec = get_odds_decimal(update['oddsTaken'])

    if adv_dec and taken_dec:
        if taken_dec > adv_dec:
            format_cell_range(ws_trans, f"L{row_idx}", CellFormat(backgroundColor=GREEN))
        elif taken_dec < adv_dec:
            format_cell_range(ws_trans, f"L{row_idx}", CellFormat(backgroundColor=RED))

    # 4. Apply Bookmaker Formatting
    # Look for the bookmaker in Config sheet (Column B) to grab its style
    config_bookies = ws_config.col_values(2) # Column B is Bookmaker_List
    try:
        # Find which row in Config has this bookmaker
        config_row_idx = config_bookies.index(update['bookmaker']) + 1
        # Get the format of that specific cell
        fmt = get_user_entered_format(ws_config, f"B{config_row_idx}")
        
        if fmt:
            # Apply that format to the Bookmaker cell in Transactions (Column K)
            format_cell_range(ws_trans, f"K{row_idx}", fmt)
    except ValueError:
        pass # Bookmaker not in list, skip formatting

    return True, "Success"

def settle_bet_row(sh, settle: dict):
    ws = sh.worksheet("Transactions")
    ids = ws.col_values(1)
    
    try:
        row_idx = ids.index(settle['ID']) + 1
    except ValueError:
        return False, "ID not found"

    # Tweak: If rule4 is 0 or None, make it an empty string
    r4_val = settle['rule4'] if settle['rule4'] and settle['rule4'] != 0 else ""

    settle_values = [
        settle['status'],
        settle['position'],
        settle['sp'],
        r4_val
    ]
    
    ws.update(range_name=f"Q{row_idx}:T{row_idx}", 
              values=[settle_values], 
              value_input_option='USER_ENTERED')
    
    if settle['comment']:
        ws.update_acell(f"AJ{row_idx}", settle['comment'])

    # 1. SP Analysis (Column S vs Column I)
    advised_str = ws.acell(f"I{row_idx}").value
    adv_dec = get_odds_decimal(advised_str)
    sp_dec = get_odds_decimal(settle['sp'])

    if adv_dec and sp_dec:
        if sp_dec < adv_dec: # Price shortened = Good value found
            format_cell_range(ws, f"S{row_idx}", CellFormat(backgroundColor=GREEN))
        elif sp_dec > adv_dec: # Price drifted = Poor value
            format_cell_range(ws, f"S{row_idx}", CellFormat(backgroundColor=RED))

    # 2. Profit Highlights (Columns AF:AI)
    # We apply this if status is Won or Placed (Profit >= 0)
    if settle['status'] in ["Won", "Placed"]:
        # Note: If it's a "Void", we usually leave it neutral
        format_cell_range(ws, f"AF{row_idx}:AI{row_idx}", CellFormat(backgroundColor=GREEN))
        
    return True, "Settled with visual highlights"

# The headers corresponding to columns U through AE
EXCLUDED_COLUMNS = {
    "Year", "Month", "DO", "DO (BOG)", "DO (W)", 
    "PlcFr", "DO (P)", "TotalStake (Pts)", 
    "TotalStake (£)", "Ret (WL)", "Ret (PL)"
}

def get_filtered_bets(sh, status_filter=None, tipster_filter=None):
    ws = sh.worksheet("Transactions")
    all_records = ws.get_all_records()
    
    filtered_results = []
    for record in all_records:
        # 1. Apply Filters
        if status_filter and record.get("Status") != status_filter:
            continue
        if tipster_filter and record.get("Tipster") != tipster_filter:
            continue
            
        # 2. Strip "Hidden" Calculation Keys
        # We use a dictionary comprehension to build a new record 
        # that only includes keys NOT in our exclusion list
        clean_record = {
            k: v for k, v in record.items() 
            if k not in EXCLUDED_COLUMNS
        }
        
        filtered_results.append(clean_record)
        
    return filtered_results

def amend_bet_row(sh, updates: dict) -> tuple[bool, str]:
    ws = sh.worksheet("Transactions")
    ids = ws.col_values(1)
    
    try:
        row_idx = ids.index(updates['ID']) + 1
    except ValueError:
        return False, "ID not found"

    column_mapping = {
        "raceDate": "B",
        "stakePts": "G",
        "gbpPerPoint": "P",
        "rule4": "T",
        "returnsPts": "AF",
        "profitPts": "AG",
        "returnsGbp": "AH",
        "profitGbp": "AI",
        "comment": "AJ"
    }

    batch_payload = []
    overwritten_calc_columns = [] # Keep track of overridden calculation columns
    
    # Check if we are overwriting calculated fields
    for k in ["returnsPts", "profitPts", "returnsGbp", "profitGbp"]:
        if updates.get(k) is not None:
            overwritten_calc_columns.append(column_mapping[k])
    
    if overwritten_calc_columns and not updates.get("comment"):
        return False, "A comment is required when overwriting calculated profit or return columns."

    for key, column_letter in column_mapping.items():
        value = updates.get(key)
        if value is not None:
            if key == "rule4" and value == 0:
                value = ""
                
            batch_payload.append({
                "range": f"{column_letter}{row_idx}",
                "values": [[value]]
            })

    if not batch_payload:
        return False, "No valid update parameters were passed."

    # 1. Commit the data updates
    ws.batch_update(batch_payload, value_input_option='USER_ENTERED')
    
    # 2. Apply formatting to overridden calculation cells
    if overwritten_calc_columns:
        for col_letter in overwritten_calc_columns:
            # Applies dark blue text color and sets font style to italic
            format_cell_range(ws, f"{col_letter}{row_idx}", AMENDED_FORMAT)

    return True, f"Successfully updated {len(batch_payload)} fields on row {row_idx}."
