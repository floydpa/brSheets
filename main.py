from dotenv import load_dotenv
load_dotenv()  # This looks for a .env file and loads it into os.environ

import os
import json
import re
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from typing import List, Optional
from schemas import DraftBet, OpenBetUpdate, SettleBet, AmendBet
from sheets import get_user_sheet, insert_draft_row, settle_bet_row, update_to_open
from sheets import settle_bet_row, get_filtered_bets, amend_bet_row

from database import SessionLocal, init_db, TipDetail, TipMessage
from sqlalchemy.orm import Session
from fastapi import Depends

from fastapi import Path as FastPath
import rp_scraper


# Load user mapping from environment: e.g. '{"token123": "sheet_id_A", "token456": "sheet_id_B"}'
USER_SHEETS_JSON = os.environ.get("USER_SHEETS_CONFIG", "{}")
USER_SHEETS = json.loads(USER_SHEETS_JSON)

# USER_SHEETS contains sensitive mappings of user tokens to their Google Sheet IDs.
# The definition looks like this:
# USER_SHEETS = {
#    "secret_token_1": "Google Sheet ID for User 1",
#    "secret_token_2": "Google Sheet ID for User 2"
#}

app = FastAPI()

# Initialize DB (creates the .db file and tables if they don't exist)
init_db()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

@app.patch("/bet/amend")
async def amend_bet(update: AmendBet, x_token: str = Header(None)):
    sheet_id = USER_SHEETS.get(x_token)
    if not sheet_id:
        raise HTTPException(status_code=401, detail="Invalid User Token")
    
    sh = get_user_sheet(sheet_id)
    success, message = amend_bet_row(sh, update.model_dump())
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"status": "success", "message": message}

@app.get("/bets", response_model=List[dict])
def get_bets(
    status: Optional[str] = None, 
    tipster: Optional[str] = None, 
    x_token: str = Header(None)
):
    sheet_id = USER_SHEETS.get(x_token)
    if not sheet_id:
        raise HTTPException(status_code=401, detail="Invalid User Token")
    
    sh = get_user_sheet(sheet_id)
    # We'll build this function next
    return get_filtered_bets(sh, status, tipster)

@app.get("/tips")
def list_tips(db: Session = Depends(get_db)):
    # Returns all parsed tips, joining with the parent message to get 'arrived_at'
    tips = db.query(TipDetail).all()
    return tips

@app.get("/tips/{msg_id}")
def get_tip_by_msg(msg_id: int, db: Session = Depends(get_db)):
    tip = db.query(TipMessage).filter(TipMessage.msg_id == msg_id).first()
    if not tip:
        raise HTTPException(status_code=404, detail="Message not found")
    return tip

@app.get("/results/{date}/{course}/{time}")
async def get_racing_post_results(
    date: str = FastPath(..., description="Date formatted as DD-MM-YYYY"),
    course: str = FastPath(..., description="Name of the course, e.g., York"),
    time: str = FastPath(..., description="Race off-time in 24h format HH:MM")
):
    # Regex validate date parameter to head off bad input loops early
    if not re.match(r"^\d{2}-\d{2}-\d{4}$", date):
        raise HTTPException(status_code=400, detail="Invalid date layout format. Must be DD-MM-YYYY.")
        
    if not re.match(r"^\d{2}:\d{2}$", time):
        raise HTTPException(status_code=400, detail="Invalid time layout format. Must be HH:MM.")

    result_payload = await rp_scraper.fetch_race_results(date, course, time)
    
    if result_payload["status"] == "error":
        raise HTTPException(status_code=404, detail=result_payload["message"])
        
    return result_payload["data"]
