# Integration with SQLite via SQLAlchemy for bet tracking.
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

from utils import generate_oddschecker_url

# SQLite database file
DATABASE_URL = "sqlite:///./br_sheets.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TipMessage(Base):
    __tablename__ = "tip_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer)
    msg_id = Column(Integer, index=True) # Unique within chat
    service_name = Column(String, default="TOF")
    arrived_at = Column(DateTime, default=datetime.datetime.utcnow)
    raw_text = Column(Text)
    
    # Relationship to individual bets
    tips = relationship("TipDetail", back_populates="parent_message")

class TipDetail(Base):
    __tablename__ = "tip_details"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("tip_messages.id"))
    
    # Flags & Content
    is_amended = Column(Boolean, default=False)
    msg_tip_summary = Column(Text)   # Original one-liner
    parsed_summary = Column(Text)    # Constructed summary
    detail_text = Column(Text, nullable=True)
    
    # Parsed Data Points
    race_date = Column(String)       # YYYY-MM-DD
    race_time = Column(String)       # HH:MM
    horse_name = Column(String)
    stake_pts = Column(Float)
    bet_type = Column(String)        # "win" or "ew"
    adv_odds = Column(String)
    adv_places = Column(Integer, nullable=True)

    parent_message = relationship("TipMessage", back_populates="tips")

    @property
    def oddschecker_url(self):
        return generate_oddschecker_url(self.race_date, self.horse_name, self.race_time)


# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
