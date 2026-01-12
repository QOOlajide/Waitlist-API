from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db, get_engine
from app.models import WaitlistIn, WaitlistOut
from app.service import add_to_waitlist

router = APIRouter()

@router.get("/")
def root():
    return {
        "name": "Waitlist API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }

@router.get("/health")
def health():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

@router.post("/waitlist", response_model=WaitlistOut, status_code=201)
def join_waitlist(payload: WaitlistIn, db: Session = Depends(get_db)):
    return add_to_waitlist(db, payload)
