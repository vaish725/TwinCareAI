from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from .database import Base # Assuming Base is defined in database.py

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True) # UUID for session ID
    patient_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String, default="created") # e.g., created, running, completed, failed, partial_failure
    initial_context = Column(Text) # Store JSON string of initial context
    results = Column(Text, nullable=True) # Store JSON string of final results
    trace = Column(Text, nullable=True) # Store JSON string of orchestration trace
    errors = Column(Text, nullable=True) # Store JSON string of errors
