from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
import os
from dotenv import load_dotenv

load_dotenv()

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(_BACKEND_DIR, 'hcp_crm.db').replace(os.sep, '/')}")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class InteractionType(str, enum.Enum):
    MEETING = "Meeting"
    CALL = "Call"
    CONFERENCE = "Conference"
    EMAIL = "Email"
    OTHER = "Other"

class Sentiment(str, enum.Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"

class HCPInteraction(Base):
    __tablename__ = "hcp_interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), nullable=False)
    interaction_type = Column(String(50), default="Meeting")
    date = Column(String(50))
    time = Column(String(50))
    attendees = Column(Text)
    topics_discussed = Column(Text)
    voice_note_summary = Column(Text)
    materials_shared = Column(Text)
    samples_distributed = Column(Text)
    hcp_sentiment = Column(String(50), default="Neutral")
    outcomes = Column(Text)
    follow_up_actions = Column(Text)
    raw_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
