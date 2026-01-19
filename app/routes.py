import csv
import io
import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db, get_engine
from app.email import send_welcome_email
from app.models import WaitlistIn, WaitlistOut
from app.models_db import WaitlistEntry
from app.service import add_to_waitlist

router = APIRouter()

# Admin API key for protected endpoints
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


def verify_admin_key(key: str = Query(..., description="Admin API key")):
    """Verify the admin API key from query parameter."""
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY not configured")
    if key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


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


@router.get("/admin/export")
def export_waitlist_csv(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_key),
):
    """
    Export all waitlist entries as CSV.
    
    Requires admin API key: ?key=YOUR_ADMIN_KEY
    """
    # Query all entries ordered by signup date
    entries = db.query(WaitlistEntry).order_by(WaitlistEntry.created_at.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow(["id", "email", "source", "created_at"])
    
    # Data rows
    for entry in entries:
        writer.writerow([
            entry.id,
            entry.email,
            entry.source or "",
            entry.created_at.isoformat() if entry.created_at else "",
        ])
    
    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"waitlist_export_{timestamp}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
