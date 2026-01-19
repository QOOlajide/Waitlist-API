from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db, get_engine
from app.email import send_welcome_email
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
def join_waitlist(
    payload: WaitlistIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    result = add_to_waitlist(db, payload)

    # Queue welcome email (non-blocking)
    background_tasks.add_task(send_welcome_email, result["email"])

    return result
