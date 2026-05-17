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

class AmendBet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ID: str
    raceDate: Optional[str] = None     # DD/MM/YYYY
    stakePts: Optional[float] = None
    gbpPerPoint: Optional[float] = None # Maps to column P
    rule4: Optional[int] = None        # Maps to column T (Use 0 or integer)
    returnsPts: Optional[float] = None # Column AF (Overwrites formula)
    profitPts: Optional[float] = None  # Column AG (Overwrites formula)
    returnsGbp: Optional[float] = None # Column AH (Overwrites formula)
    profitGbp: Optional[float] = None  # Column AI (Overwrites formula)
    comment: Optional[str] = None      # Column AJ (Highly recommended for overrides)
