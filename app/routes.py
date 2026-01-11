from fastapi import APIRouter
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
    return {"status": "ok"}

@router.post("/waitlist", response_model=WaitlistOut, status_code=201)
def join_waitlist(payload: WaitlistIn):
    return add_to_waitlist(payload)
