from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from schemas import DraftBet, OpenBetUpdate, SettleBet
from sheets import get_user_sheet, insert_draft_row, update_to_open, settle_bet_row
from confidential import USER_SHEETS

app = FastAPI()

# USER_SHEETS contains sensitive mappings of user tokens to their Google Sheet IDs.
# The definition looks like this:
# USER_SHEETS = {
#    "secret_token_1": "Google Sheet ID for User 1",
#    "secret_token_2": "Google Sheet ID for User 2"
#}

@app.post("/bet/draft")
async def create_draft(bet: DraftBet, background_tasks: BackgroundTasks, x_token: str = Header(None)):
    sheet_id = USER_SHEETS.get(x_token)
    if not sheet_id:
        raise HTTPException(status_code=401, detail="Invalid User Token")
    
    # We fetch the sheet object now to ensure the ID is valid...
    sh = get_user_sheet(sheet_id)
    
    # ...but we "schedule" the slow writing part for later
    background_tasks.add_task(insert_draft_row, sh, bet.model_dump())
    
    # The API returns THIS immediately
    return {"status": "accepted", "message": "Bet is being processed in the background"}

@app.post("/bet/open")
async def open_bet(update: OpenBetUpdate, x_token: str = Header(None)):
    sheet_id = USER_SHEETS.get(x_token)
    if not sheet_id:
        raise HTTPException(status_code=401, detail="Invalid User Token")
    
    sh = get_user_sheet(sheet_id)
    success, message = update_to_open(sh, update.model_dump())
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
        
    return {"status": "success", "message": "Bet updated to Open and formatted"}

@app.post("/bet/settle")
async def settle_bet(settle: SettleBet, x_token: str = Header(None)):
    sheet_id = USER_SHEETS.get(x_token)
    if not sheet_id:
        raise HTTPException(status_code=401, detail="Invalid User Token")
    
    sh = get_user_sheet(sheet_id)
    success, message = settle_bet_row(sh, settle.model_dump())
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
        
    return {"status": "success", "message": message}
