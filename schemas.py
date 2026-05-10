from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class DraftBet(BaseModel):
    model_config = ConfigDict(extra="ignore") # This skips tipSent/tipSummary
    ID: str
    raceDate: str
    racecourse: str
    raceTime: str
    horse: str
    tipster: str
    stakePts: float
    betType: str
    advisedOdds: str
    advisedPlaces: Optional[str] = ""

class DraftBet(BaseModel):
    model_config = ConfigDict(extra="ignore")   
    ID: str
    raceDate: str  # DD/MM/YYYY
    racecourse: str
    raceTime: str  # HH:MM
    horse: str
    tipster: str
    stakePts: float
    betType: str  # "Win" or "E/W"
    advisedOdds: str
    advisedPlaces: Optional[str] = ""

class OpenBetUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ID: str
    bookmaker: str
    oddsTaken: str
    bog: str
    placesPaid: str
    placeFraction: str
    gbpPerPoint: float

class SettleBet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ID: str
    status: str  # Won, Placed, Lost, Void
    position: str # Numeric (1, 2...) or codes (PU, NR, etc.)
    sp: str       # Starting Price
    rule4: Optional[int] = None # Blank  if no deduction
    comment: Optional[str] = ""
