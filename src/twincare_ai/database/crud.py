from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime

from . import models
from twincare_ai.api.main import SessionUpdate # Import Pydantic model for updates

def create_item(db: Session, name: str, description: str):
    db_item = models.Item(name=name, description=description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

# --- CRUD operations for Session ---

def create_session(db: Session, session_id: str, patient_id: str, initial_context: Dict[str, Any]):
    db_session = models.Session(
        id=session_id,
        patient_id=patient_id,
        initial_context=json.dumps(initial_context),
        status="created",
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: str):
    return db.query(models.Session).filter(models.Session.id == session_id).first()

def update_session(db: Session, session_id: str, session_update: SessionUpdate):
    db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if db_session:
        update_data = session_update.model_dump(exclude_unset=True)
        
        if "status" in update_data: db_session.status = update_data["status"]
        if "last_updated" in update_data: db_session.last_updated = update_data["last_updated"]
        if "results" in update_data: db_session.results = json.dumps(update_data["results"])
        if "trace" in update_data: db_session.trace = json.dumps(update_data["trace"])
        if "errors" in update_data: db_session.errors = json.dumps(update_data["errors"])
        
        db.commit()
        db.refresh(db_session)
    return db_session

def get_all_sessions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Session).offset(skip).limit(limit).all()
