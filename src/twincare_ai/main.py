from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from twincare_ai.api import health, invoke
from twincare_ai.database import models, database

# Create all database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="TwinCare AI Backend",
    description="API for TwinCare AI, a multi-agent healthcare simulation system.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(invoke.router)

# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to TwinCare AI API!"}

